"""Seed de datos de prueba para desarrollo."""

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.core.config import settings
from app.core.security import hash_password
from app.models.base import Base
from app.models.tenant import Tenant
from app.models.user import User, Role


TENANT = {"name": "Aseguradora Demo", "slug": "demo"}

USERS = [
    {"email": "admin@demo.com",      "password": "Admin123!", "full_name": "Admin Demo",      "role": Role.ADMIN},
    {"email": "supervisor@demo.com", "password": "Admin123!", "full_name": "Supervisor Demo", "role": Role.SUPERVISOR},
    {"email": "analista@demo.com",   "password": "Admin123!", "full_name": "Analista Demo",   "role": Role.ANALYST},
]


async def seed() -> None:
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async with session_factory() as db:
        # Tenant
        from sqlalchemy import select
        existing = await db.execute(select(Tenant).where(Tenant.slug == TENANT["slug"]))
        tenant = existing.scalar_one_or_none()
        if not tenant:
            tenant = Tenant(**TENANT)
            db.add(tenant)
            await db.flush()
            print(f"✅ Tenant creado: {tenant.name} (slug={tenant.slug})")
        else:
            print(f"⚠️  Tenant ya existe: {tenant.slug}")

        # Usuarios
        for u in USERS:
            existing_user = await db.execute(
                select(User).where(User.email == u["email"], User.tenant_id == tenant.id)
            )
            if existing_user.scalar_one_or_none():
                print(f"⚠️  Usuario ya existe: {u['email']}")
                continue
            user = User(
                email=u["email"],
                hashed_password=hash_password(u["password"]),
                full_name=u["full_name"],
                role=u["role"],
                tenant_id=tenant.id,
            )
            db.add(user)
            print(f"✅ Usuario creado: {u['email']} ({u['role'].value}) — pass: {u['password']}")

        await db.commit()

    await engine.dispose()
    print("\n🎉 Seed completado.")


if __name__ == "__main__":
    asyncio.run(seed())
