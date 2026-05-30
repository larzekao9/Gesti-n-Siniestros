"""Authentication domain service.

All auth business logic lives here – routers only orchestrate HTTP I/O.
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
    generate_totp_secret,
    get_totp_uri,
    hash_password,
    verify_password,
    verify_totp,
)
from app.models.password_reset_token import PasswordResetToken
from app.models.refresh_token import RefreshToken
from app.models.tenant import Tenant
from app.models.user import User
from app.services.email_service import EmailService
from app.services.exceptions import (
    AuthenticationError,
    ConflictError,
    NotFoundError,
    ValidationError,
)


class AuthService:
    """Authentication and user session management."""

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------

    async def _get_tenant(self, db: AsyncSession, slug: str) -> Tenant:
        result = await db.execute(
            select(Tenant).where(Tenant.slug == slug)
        )
        tenant = result.scalar_one_or_none()
        if tenant is None:
            raise NotFoundError(f"Tenant '{slug}' no encontrado")
        return tenant

    async def _get_user_by_email(
        self, db: AsyncSession, email: str, tenant_id: UUID
    ) -> User | None:
        result = await db.execute(
            select(User).where(User.email == email, User.tenant_id == tenant_id)
        )
        return result.scalar_one_or_none()

    async def _persist_refresh_token(
        self, db: AsyncSession, token: str, user: User
    ) -> RefreshToken:
        expires_at = datetime.now(timezone.utc) + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )
        record = RefreshToken(
            token=token,
            user_id=user.id,
            tenant_id=user.tenant_id,
            expires_at=expires_at,
        )
        db.add(record)
        await db.commit()
        await db.refresh(record)
        return record

    def _build_token_response(
        self, user: User, refresh_token_str: str
    ) -> dict:
        access_token = create_access_token(
            {"sub": str(user.id), "tenant_id": str(user.tenant_id)}
        )
        return {
            "access_token": access_token,
            "refresh_token": refresh_token_str,
            "token_type": "bearer",
            "user": {
                "id": str(user.id),
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role.value if hasattr(user.role, "value") else user.role,
                "mfa_enabled": user.mfa_enabled,
                "tenant_id": str(user.tenant_id),
            },
        }

    # ------------------------------------------------------------------
    # register
    # ------------------------------------------------------------------

    async def register(
        self,
        db: AsyncSession,
        *,
        email: str,
        password: str,
        full_name: str,
        tenant_slug: str,
    ) -> dict:
        tenant = await self._get_tenant(db, tenant_slug)

        existing = await self._get_user_by_email(db, email, tenant.id)
        if existing is not None:
            raise ConflictError("El email ya está registrado en este tenant")

        user = User(
            email=email,
            hashed_password=hash_password(password),
            full_name=full_name,
            tenant_id=tenant.id,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

        raw_refresh = _create_refresh_jwt(
            {"sub": str(user.id), "tenant_id": str(user.tenant_id)}
        )
        await self._persist_refresh_token(db, raw_refresh, user)

        return self._build_token_response(user, raw_refresh)

    # ------------------------------------------------------------------
    # login
    # ------------------------------------------------------------------

    async def login(
        self,
        db: AsyncSession,
        *,
        email: str,
        password: str,
        tenant_slug: str,
        mfa_code: str | None = None,
    ) -> dict:
        tenant = await self._get_tenant(db, tenant_slug)

        user = await self._get_user_by_email(db, email, tenant.id)
        if user is None or not verify_password(password, user.hashed_password):
            raise AuthenticationError("Credenciales inválidas")

        if not user.is_active:
            raise AuthenticationError("Cuenta desactivada")

        if user.mfa_enabled:
            if mfa_code is None:
                return {"mfa_required": True}
            if user.mfa_secret is None or not verify_totp(user.mfa_secret, mfa_code):
                raise AuthenticationError("Código MFA inválido")

        raw_refresh = _create_refresh_jwt(
            {"sub": str(user.id), "tenant_id": str(user.tenant_id)}
        )
        await self._persist_refresh_token(db, raw_refresh, user)

        return self._build_token_response(user, raw_refresh)

    # ------------------------------------------------------------------
    # refresh
    # ------------------------------------------------------------------

    async def refresh(self, db: AsyncSession, refresh_token: str) -> dict:
        decode_token(refresh_token)

        result = await db.execute(
            select(RefreshToken).where(RefreshToken.token == refresh_token)
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
        await db.commit()

        result = await db.execute(select(User).where(User.id == db_token.user_id))
        user = result.scalar_one_or_none()
        if user is None or not user.is_active:
            raise AuthenticationError("Usuario no encontrado o inactivo")

        new_access = create_access_token(
            {"sub": str(user.id), "tenant_id": str(user.tenant_id)}
        )
        return {"access_token": new_access, "token_type": "bearer"}

    # ------------------------------------------------------------------
    # logout
    # ------------------------------------------------------------------

    async def logout(self, db: AsyncSession, refresh_token: str) -> None:
        result = await db.execute(
            select(RefreshToken).where(RefreshToken.token == refresh_token)
        )
        db_token = result.scalar_one_or_none()
        if db_token is not None and not db_token.revoked:
            db_token.revoked = True
            await db.commit()

    # ------------------------------------------------------------------
    # MFA setup
    # ------------------------------------------------------------------

    async def setup_mfa(self, db: AsyncSession, user: User) -> dict:
        secret = generate_totp_secret()
        user.mfa_secret = secret
        await db.commit()
        qr_uri = get_totp_uri(secret, user.email)
        return {"secret": secret, "qr_uri": qr_uri}

    # ------------------------------------------------------------------
    # MFA verify
    # ------------------------------------------------------------------

    async def verify_mfa(self, db: AsyncSession, user: User, code: str) -> None:
        if user.mfa_secret is None:
            raise ValidationError(
                "MFA setup no iniciado. Llame primero a /auth/mfa/setup"
            )
        if not verify_totp(user.mfa_secret, code):
            raise ValidationError("Código TOTP inválido")
        user.mfa_enabled = True
        await db.commit()

    # ------------------------------------------------------------------
    # get current user (for /me)
    # ------------------------------------------------------------------

    async def get_me(self, db: AsyncSession, user: User) -> dict:
        return {
            "id": str(user.id),
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role.value if hasattr(user.role, "value") else user.role,
            "mfa_enabled": user.mfa_enabled,
            "tenant_id": str(user.tenant_id),
            "is_active": user.is_active,
        }

    # ------------------------------------------------------------------
    # password reset (CU-28)
    # ------------------------------------------------------------------

    _email_service = EmailService()

    async def request_password_reset(
        self,
        db: AsyncSession,
        *,
        email: str,
        tenant_slug: str,
        frontend_base_url: str = "http://localhost:3000",
    ) -> None:
        tenant = await self._get_tenant(db, tenant_slug)
        user = await self._get_user_by_email(db, email, tenant.id)

        # Always return 200 to prevent email enumeration
        if user is None or not user.is_active:
            return

        token_value = secrets.token_urlsafe(32)
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=15)

        reset = PasswordResetToken(
            user_id=user.id,
            tenant_id=user.tenant_id,
            token=token_value,
            expires_at=expires_at,
        )
        db.add(reset)
        await db.commit()

        reset_link = f"{frontend_base_url}/reset-password?token={token_value}"
        await self._email_service.send_password_reset(
            to_email=user.email, reset_link=reset_link
        )

    async def confirm_password_reset(
        self, db: AsyncSession, *, token: str, new_password: str
    ) -> None:
        result = await db.execute(
            select(PasswordResetToken).where(PasswordResetToken.token == token)
        )
        reset = result.scalar_one_or_none()

        if reset is None:
            raise ValidationError("Token inválido o expirado")

        if reset.used_at is not None:
            raise ValidationError("Token inválido o expirado")

        stored_exp = reset.expires_at
        if stored_exp.tzinfo is None:
            stored_exp = stored_exp.replace(tzinfo=timezone.utc)
        if stored_exp < datetime.now(timezone.utc):
            raise ValidationError("Token inválido o expirado")

        result = await db.execute(select(User).where(User.id == reset.user_id))
        user = result.scalar_one_or_none()
        if user is None or not user.is_active:
            raise NotFoundError("Usuario no encontrado o inactivo")

        user.hashed_password = hash_password(new_password)
        reset.used_at = datetime.now(timezone.utc)

        # Revoke all refresh tokens for this user (force re-login)
        await db.execute(
            update(RefreshToken)
            .where(RefreshToken.user_id == user.id, RefreshToken.revoked.is_(False))
            .values(revoked=True)
        )

        await db.commit()

    # ------------------------------------------------------------------
    # change password (CU-29)
    # ------------------------------------------------------------------

    async def change_password(
        self,
        db: AsyncSession,
        user: User,
        *,
        current_password: str,
        new_password: str,
    ) -> None:
        if not verify_password(current_password, user.hashed_password):
            raise AuthenticationError("Contraseña actual incorrecta")

        if verify_password(new_password, user.hashed_password):
            raise ValidationError("La nueva contraseña debe ser diferente a la actual")

        user.hashed_password = hash_password(new_password)

        # Revoke all OTHER refresh tokens (keep current session)
        await db.execute(
            update(RefreshToken)
            .where(
                RefreshToken.user_id == user.id,
                RefreshToken.revoked.is_(False),
            )
            .values(revoked=True)
        )

        await db.commit()
