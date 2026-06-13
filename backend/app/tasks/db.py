"""Acceso a BD desde Celery tasks (patrón Ciclo 8 — Context.md §6 ⚠1/⚠2).

Celery corre sync; la app es SQLAlchemy async. Patrón único:

- Cada task envuelve su corutina con ``run_async`` (``asyncio.run``).
- ``task_session`` crea un engine async PROPIO con ``NullPool`` y lo
  desecha al final: nunca se comparte pool/event-loop entre el proceso
  web y el worker (ni entre invocaciones tras un fork de Celery).
- Las tasks NO tienen request ni middleware de tenant: reciben
  ``tenant_id`` explícito en sus argumentos y filtran por él SIEMPRE.
"""

import asyncio
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import settings


def run_async(coro):
    """Ejecuta una corutina desde el contexto sync de una Celery task."""
    return asyncio.run(coro)


@asynccontextmanager
async def task_session():
    """Sesión async aislada para una task. Commit al salir sin excepción."""
    engine = create_async_engine(settings.DATABASE_URL, poolclass=NullPool)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    try:
        async with factory() as session:
            yield session
            await session.commit()
    finally:
        await engine.dispose()
