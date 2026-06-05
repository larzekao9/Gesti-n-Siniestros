"""Seed del canal asegurado (Ciclo 7) para probar la app móvil.

Crea:
  1) Una cuenta ACTIVA lista para login directo (Juan Pérez).
  2) Una cuenta PENDIENTE con activation_token (María) para probar la pantalla
     de activación con código.

Idempotente: se puede correr varias veces. Requiere haber corrido seed.py antes
(necesita tenant 'demo' + policyholders + pólizas + vehículos).

Uso:
  docker compose exec backend bash -c "cd /app && PYTHONPATH=/app python scripts/seed_insured.py"
"""

import asyncio
import secrets
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.config import settings
from app.core.security import hash_password
from app.models.policyholder import Policyholder
from app.models.policyholder_account import PolicyholderAccount
from app.models.tenant import Tenant

# Identificamos por document_id (estable) y usamos el email real de cada fila.
ACTIVE_DOC = "12345678-LP"  # Juan Pérez
ACTIVE_PASSWORD = "Asegurado123!"
PENDING_DOC = "87654321-CB"  # María Gómez


async def _get_account(db, *, tenant_id, policyholder_id):
    return (
        await db.execute(
            select(PolicyholderAccount).where(
                PolicyholderAccount.policyholder_id == policyholder_id,
                PolicyholderAccount.tenant_id == tenant_id,
            )
        )
    ).scalar_one_or_none()


async def main() -> None:
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async with session_factory() as db:
        tenant = (
            await db.execute(select(Tenant).where(Tenant.slug == "demo"))
        ).scalar_one_or_none()
        if not tenant:
            print("❌ No existe el tenant 'demo'. Corré primero scripts/seed.py")
            return

        # ── 1) Cuenta activa (login directo) ──────────────────────────
        juan = (
            await db.execute(
                select(Policyholder).where(
                    Policyholder.document_id == ACTIVE_DOC,
                    Policyholder.tenant_id == tenant.id,
                )
            )
        ).scalar_one_or_none()
        if not juan:
            print(f"❌ No se encontró el asegurado {ACTIVE_DOC}. Corré seed.py")
            return
        active_email = juan.email or f"{ACTIVE_DOC.lower()}@demo.com"

        acc = await _get_account(db, tenant_id=tenant.id, policyholder_id=juan.id)
        if acc is None:
            acc = PolicyholderAccount(
                tenant_id=tenant.id,
                policyholder_id=juan.id,
                email=active_email,
                is_active=True,
                hashed_password=hash_password(ACTIVE_PASSWORD),
            )
            db.add(acc)
        else:
            acc.email = active_email
            acc.is_active = True
            acc.hashed_password = hash_password(ACTIVE_PASSWORD)
            acc.activation_token = None
            acc.activation_expires_at = None
        await db.flush()

        # ── 2) Cuenta pendiente con token de activación ───────────────
        maria = (
            await db.execute(
                select(Policyholder).where(
                    Policyholder.document_id == PENDING_DOC,
                    Policyholder.tenant_id == tenant.id,
                )
            )
        ).scalar_one_or_none()
        pending_email = maria.email if maria else None
        token = None
        if maria:
            macc = await _get_account(db, tenant_id=tenant.id, policyholder_id=maria.id)
            token = secrets.token_urlsafe(32)
            expires = datetime.now(timezone.utc) + timedelta(days=7)
            if macc is None:
                macc = PolicyholderAccount(
                    tenant_id=tenant.id,
                    policyholder_id=maria.id,
                    email=maria.email,
                    is_active=False,
                    activation_token=token,
                    activation_expires_at=expires,
                )
                db.add(macc)
            else:
                macc.is_active = False
                macc.hashed_password = None
                macc.activation_token = token
                macc.activation_expires_at = expires
            await db.flush()

        await db.commit()

    await engine.dispose()

    print("\n" + "=" * 60)
    print("✅ Canal asegurado listo para probar")
    print("=" * 60)
    print("\n▶ LOGIN DIRECTO (pantalla 'Ingresá a tu cuenta'):")
    print(f"   Aseguradora : demo")
    print(f"   Email       : {active_email}")
    print(f"   Contraseña  : {ACTIVE_PASSWORD}")
    if token:
        print("\n▶ ACTIVACIÓN CON CÓDIGO (pantalla 'Activá tu cuenta'):")
        print(f"   Email del asegurado: {pending_email}")
        print(f"   Código de activación:\n   {token}")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
