"""Insured authentication domain service (canal asegurado — CU-01).

Espejo de :class:`AuthService` pero para ``policyholder_accounts``. Toda la lógica
de auth del asegurado vive acá; el router solo orquesta. Los tokens de acceso
llevan ``scope='insured'`` para distinguirlos del canal interno.
"""

import secrets
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token as _create_refresh_jwt,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.account_refresh_token import AccountRefreshToken
from app.models.device_token import DevicePlatform, DeviceToken
from app.models.policyholder import Policyholder
from app.models.policyholder_account import PolicyholderAccount
from app.models.tenant import Tenant
from app.services.audit_service import AuditService
from app.services.exceptions import (
    AuthenticationError,
    ConflictError,
    NotFoundError,
    ValidationError,
)

audit_service = AuditService()

# TTL de la invitación de activación (single-use). 7 días — razonable para que el
# asegurado active su cuenta sin que el token quede vivo indefinidamente.
ACTIVATION_TTL = timedelta(days=7)
# TTL del token de restablecimiento de contraseña.
RESET_TTL = timedelta(minutes=30)


class InsuredAuthService:
    """Auth y sesión del canal asegurado."""

    # ── helpers ───────────────────────────────────────────────────────

    async def _get_tenant(self, db: AsyncSession, slug: str) -> Tenant:
        result = await db.execute(select(Tenant).where(Tenant.slug == slug))
        tenant = result.scalar_one_or_none()
        if tenant is None:
            raise NotFoundError(f"Tenant '{slug}' no encontrado")
        return tenant

    async def _get_account_by_email(
        self, db: AsyncSession, email: str, tenant_id: UUID
    ) -> PolicyholderAccount | None:
        result = await db.execute(
            select(PolicyholderAccount).where(
                PolicyholderAccount.email == email,
                PolicyholderAccount.tenant_id == tenant_id,
            )
        )
        return result.scalar_one_or_none()

    async def _persist_refresh_token(
        self, db: AsyncSession, token: str, account: PolicyholderAccount
    ) -> AccountRefreshToken:
        # Canal asegurado: refresh de larga vida (sesión "hasta logout"),
        # separado del staff interno (settings.REFRESH_TOKEN_EXPIRE_DAYS).
        expires_at = datetime.now(timezone.utc) + timedelta(
            days=settings.INSURED_REFRESH_TOKEN_EXPIRE_DAYS
        )
        record = AccountRefreshToken(
            token=token,
            account_id=account.id,
            tenant_id=account.tenant_id,
            expires_at=expires_at,
        )
        db.add(record)
        await db.flush()
        return record

    def _build_token_response(
        self, account: PolicyholderAccount, refresh_token_str: str
    ) -> dict:
        access_token = create_access_token(
            {
                "sub": str(account.id),
                "tenant_id": str(account.tenant_id),
                "scope": "insured",
            }
        )
        return {
            "access_token": access_token,
            "refresh_token": refresh_token_str,
            "token_type": "bearer",
            "account": account,
        }

    # ── invitación (CU-01 F-A1) ───────────────────────────────────────

    async def create_invitation(
        self,
        db: AsyncSession,
        *,
        policyholder_id: UUID,
        tenant_id: UUID,
        actor_user_id: UUID,
    ) -> PolicyholderAccount:
        """Genera (o regenera) el activation_token para un policyholder.

        El asegurado debe tener un email registrado. Si ya existe una cuenta
        activa, no se puede reinvitar (409). Si existe una cuenta pendiente, se
        regenera el token. NO envía mail (alcance Ciclo 7) — el token se devuelve
        en la respuesta del endpoint.
        """
        ph = await db.execute(
            select(Policyholder).where(
                Policyholder.id == policyholder_id,
                Policyholder.tenant_id == tenant_id,
            )
        )
        ph = ph.scalar_one_or_none()
        if ph is None:
            raise NotFoundError("Asegurado no encontrado")
        if not ph.email:
            raise ValidationError(
                "El asegurado no tiene email registrado; no se puede invitar"
            )

        existing = await db.execute(
            select(PolicyholderAccount).where(
                PolicyholderAccount.policyholder_id == policyholder_id,
                PolicyholderAccount.tenant_id == tenant_id,
            )
        )
        account = existing.scalar_one_or_none()

        if account is not None and account.is_active:
            raise ConflictError("El asegurado ya tiene una cuenta activa")

        token_value = secrets.token_urlsafe(32)
        expires_at = datetime.now(timezone.utc) + ACTIVATION_TTL

        if account is None:
            account = PolicyholderAccount(
                tenant_id=tenant_id,
                policyholder_id=policyholder_id,
                email=ph.email,
                is_active=False,
                activation_token=token_value,
                activation_expires_at=expires_at,
            )
            db.add(account)
        else:
            account.activation_token = token_value
            account.activation_expires_at = expires_at
            account.email = ph.email

        await db.flush()

        await audit_service.write(
            db,
            tenant_id=tenant_id,
            action="INVITE_POLICYHOLDER",
            entity_type="policyholder_account",
            entity_id=account.id,
            actor_user_id=actor_user_id,
            payload_diff={"policyholder_id": str(policyholder_id)},
        )
        await db.refresh(account)
        return account

    # ── registro con token (CU-01 F-A1) ───────────────────────────────

    async def register_with_token(
        self, db: AsyncSession, *, activation_token: str, password: str
    ) -> dict:
        result = await db.execute(
            select(PolicyholderAccount).where(
                PolicyholderAccount.activation_token == activation_token
            )
        )
        account = result.scalar_one_or_none()
        if account is None:
            raise ValidationError("Token de activación inválido o expirado")

        if account.is_active:
            raise ConflictError("La cuenta ya fue activada")

        exp = account.activation_expires_at
        if exp is None:
            raise ValidationError("Token de activación inválido o expirado")
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=timezone.utc)
        if exp < datetime.now(timezone.utc):
            raise ValidationError("Token de activación inválido o expirado")

        account.hashed_password = hash_password(password)
        account.is_active = True
        account.activation_token = None
        account.activation_expires_at = None
        await db.flush()

        raw_refresh = _create_refresh_jwt(
            {"sub": str(account.id), "tenant_id": str(account.tenant_id), "scope": "insured"}
        )
        await self._persist_refresh_token(db, raw_refresh, account)

        await audit_service.write(
            db,
            tenant_id=account.tenant_id,
            action="INSURED_REGISTER",
            entity_type="policyholder_account",
            entity_id=account.id,
            actor_account_id=account.id,
        )
        await db.refresh(account)
        return self._build_token_response(account, raw_refresh)

    # ── login (CU-01) ─────────────────────────────────────────────────

    async def login(
        self, db: AsyncSession, *, email: str, password: str, tenant_slug: str
    ) -> dict:
        tenant = await self._get_tenant(db, tenant_slug)
        account = await self._get_account_by_email(db, email, tenant.id)

        if (
            account is None
            or account.hashed_password is None
            or not verify_password(password, account.hashed_password)
        ):
            raise AuthenticationError("Credenciales inválidas")

        if not account.is_active:
            raise AuthenticationError("Cuenta inactiva o no activada")

        raw_refresh = _create_refresh_jwt(
            {"sub": str(account.id), "tenant_id": str(account.tenant_id), "scope": "insured"}
        )
        await self._persist_refresh_token(db, raw_refresh, account)

        await audit_service.write(
            db,
            tenant_id=account.tenant_id,
            action="INSURED_LOGIN",
            entity_type="policyholder_account",
            entity_id=account.id,
            actor_account_id=account.id,
        )
        await db.refresh(account)
        return self._build_token_response(account, raw_refresh)

    # ── refresh ───────────────────────────────────────────────────────

    async def refresh(self, db: AsyncSession, refresh_token: str) -> dict:
        decode_token(refresh_token)

        result = await db.execute(
            select(AccountRefreshToken).where(
                AccountRefreshToken.token == refresh_token
            )
        )
        db_token = result.scalar_one_or_none()
        if db_token is None or db_token.revoked:
            raise AuthenticationError("Refresh token inválido o revocado")

        stored_exp = db_token.expires_at
        if stored_exp.tzinfo is None:
            stored_exp = stored_exp.replace(tzinfo=timezone.utc)
        if stored_exp < datetime.now(timezone.utc):
            raise AuthenticationError("Refresh token expirado")

        db_token.revoked = True
        await db.flush()

        result = await db.execute(
            select(PolicyholderAccount).where(
                PolicyholderAccount.id == db_token.account_id
            )
        )
        account = result.scalar_one_or_none()
        if account is None or not account.is_active:
            raise AuthenticationError("Cuenta no encontrada o inactiva")

        new_access = create_access_token(
            {"sub": str(account.id), "tenant_id": str(account.tenant_id), "scope": "insured"}
        )
        return {"access_token": new_access, "token_type": "bearer"}

    # ── logout ────────────────────────────────────────────────────────

    async def logout(self, db: AsyncSession, refresh_token: str) -> None:
        result = await db.execute(
            select(AccountRefreshToken).where(
                AccountRefreshToken.token == refresh_token
            )
        )
        db_token = result.scalar_one_or_none()
        if db_token is not None and not db_token.revoked:
            db_token.revoked = True
            await db.flush()

    # ── password reset (CU-28 canal asegurado) ────────────────────────

    async def request_password_reset(
        self, db: AsyncSession, *, email: str, tenant_slug: str
    ) -> None:
        tenant = await self._get_tenant(db, tenant_slug)
        account = await self._get_account_by_email(db, email, tenant.id)

        # Siempre 200 para no filtrar existencia de emails.
        if account is None or not account.is_active:
            return

        account.password_reset_token = secrets.token_urlsafe(32)
        account.password_reset_expires_at = datetime.now(timezone.utc) + RESET_TTL
        await db.flush()

    async def confirm_password_reset(
        self, db: AsyncSession, *, token: str, new_password: str
    ) -> None:
        result = await db.execute(
            select(PolicyholderAccount).where(
                PolicyholderAccount.password_reset_token == token
            )
        )
        account = result.scalar_one_or_none()
        if account is None:
            raise ValidationError("Token inválido o expirado")

        exp = account.password_reset_expires_at
        if exp is None:
            raise ValidationError("Token inválido o expirado")
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=timezone.utc)
        if exp < datetime.now(timezone.utc):
            raise ValidationError("Token inválido o expirado")

        account.hashed_password = hash_password(new_password)
        account.password_reset_token = None
        account.password_reset_expires_at = None

        # Revocar todos los refresh tokens de la cuenta (forzar re-login).
        await db.execute(
            update(AccountRefreshToken)
            .where(
                AccountRefreshToken.account_id == account.id,
                AccountRefreshToken.revoked.is_(False),
            )
            .values(revoked=True)
        )
        await db.flush()

    # ── device tokens (push) ──────────────────────────────────────────

    async def register_device_token(
        self,
        db: AsyncSession,
        *,
        account: PolicyholderAccount,
        expo_push_token: str,
        platform: str,
    ) -> DeviceToken:
        try:
            plat = DevicePlatform(platform)
        except ValueError:
            raise ValidationError(f"Plataforma no válida: {platform}")

        # Upsert por expo_push_token (un token físico es único).
        result = await db.execute(
            select(DeviceToken).where(DeviceToken.expo_push_token == expo_push_token)
        )
        device = result.scalar_one_or_none()
        now = datetime.now(timezone.utc)

        if device is not None:
            device.account_id = account.id
            device.tenant_id = account.tenant_id
            device.platform = plat
            device.last_seen_at = now
        else:
            device = DeviceToken(
                tenant_id=account.tenant_id,
                account_id=account.id,
                expo_push_token=expo_push_token,
                platform=plat,
                last_seen_at=now,
            )
            db.add(device)

        await db.flush()
        await db.refresh(device)
        return device

    async def unregister_device_token(
        self, db: AsyncSession, *, account: PolicyholderAccount, expo_push_token: str
    ) -> None:
        result = await db.execute(
            select(DeviceToken).where(
                DeviceToken.expo_push_token == expo_push_token,
                DeviceToken.account_id == account.id,
                DeviceToken.tenant_id == account.tenant_id,
            )
        )
        device = result.scalar_one_or_none()
        if device is not None:
            await db.delete(device)
            await db.flush()


insured_auth_service = InsuredAuthService()
