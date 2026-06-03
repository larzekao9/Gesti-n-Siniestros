"""Celery task for generating large operational reports (CU-22, F-A2).

Para la demo académica los reportes se generan de forma **síncrona** en el
endpoint ``GET /api/reports/claims`` (ver ``app/routers/reports.py``), que es
suficiente para los volúmenes esperados. Este task queda como el camino
"reportes grandes": reúsa el mismo ``ReportService`` (anti-dependencia: solo
llama al service, no duplica lógica) y deja como TODO la persistencia del
archivo + link de descarga asíncrono.
"""

import asyncio

from app.core.celery_app import celery_app
from app.core.database import AsyncSessionLocal
from app.services.report_service import report_service


@celery_app.task(name="report_generation")
def report_generation(
    tenant_id: str,
    actor_user_id: str,
    report_format: str = "pdf",
    from_date: str | None = None,
    to_date: str | None = None,
    status: str | None = None,
    analyst_id: str | None = None,
) -> dict:
    """Generate a report off the request cycle for large datasets.

    Reúsa ``ReportService.build_claims_report``. Hoy genera el archivo en
    memoria y reporta su tamaño; TODO (futuras iteraciones): subir el archivo a
    S3 vía ``StorageService`` y notificar al usuario con el link de descarga.
    """
    from datetime import date
    from uuid import UUID

    async def _run() -> dict:
        async with AsyncSessionLocal() as db:
            content, media_type, filename = await report_service.build_claims_report(
                db,
                tenant_id=UUID(tenant_id),
                actor_user_id=UUID(actor_user_id),
                report_format=report_format,
                from_date=date.fromisoformat(from_date) if from_date else None,
                to_date=date.fromisoformat(to_date) if to_date else None,
                status=status,
                analyst_id=analyst_id,
            )
            await db.commit()
            # TODO Ciclo 6+: subir `content` a S3 y enviar link via NotificationService.
            return {"status": "ok", "filename": filename, "bytes": len(content)}

    return asyncio.run(_run())
