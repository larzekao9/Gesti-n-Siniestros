"""Reports router — CU-22 (descarga PDF/Excel) + CU-37 (reportes por voz)."""

from datetime import date

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Query,
    Response,
    UploadFile,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies import require_role
from app.models.user import Role, User
from app.schemas.report import ReportInterpretRequest
from app.services.ai.report_voice_service import report_voice_service
from app.services.exceptions import ValidationError as DomainValidationError
from app.services.report_service import report_service

router = APIRouter(prefix="/reports", tags=["reports"])

# Límite defensivo para el audio (CU-37): ~25 MB, el tope de Whisper.
_MAX_AUDIO_BYTES = 25 * 1024 * 1024


@router.get("/claims")
async def generate_claims_report(
    format: str = Query("pdf", pattern="^(pdf|xlsx)$"),
    from_: date | None = Query(None, alias="from"),
    to: date | None = Query(None),
    status_: str | None = Query(None, alias="status"),
    analyst: str | None = Query(None),
    supervisor: str | None = Query(None),
    policyholder: str | None = Query(None),
    q: str | None = Query(None),
    current_user: User = require_role(Role.SUPERVISOR, Role.ADMIN),
    db: AsyncSession = Depends(get_db),
) -> Response:
    try:
        content, media_type, filename = await report_service.build_claims_report(
            db,
            tenant_id=current_user.tenant_id,
            actor_user_id=current_user.id,
            report_format=format,
            from_date=from_,
            to_date=to,
            status=status_,
            analyst_id=analyst,
            supervisor_id=supervisor,
            policyholder_id=policyholder,
            q=q,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)
        )
    await db.commit()
    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/interpret")
async def interpret_report_request(
    body: ReportInterpretRequest,
    current_user: User = require_role(Role.SUPERVISOR, Role.ADMIN),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """CU-37 — Interpreta un pedido de reporte ya en texto y devuelve los filtros.

    Sirve de fallback cuando la transcripción se hace en el cliente, y como
    contrato testeable sin audio. La generación real sigue siendo el GET de
    arriba: el frontend confirma los filtros y luego descarga.
    """
    try:
        return await report_voice_service.interpret(
            db, tenant_id=current_user.tenant_id, text=body.text
        )
    except DomainValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)
        )


@router.post("/voice")
async def interpret_report_voice(
    audio: UploadFile = File(...),
    current_user: User = require_role(Role.SUPERVISOR, Role.ADMIN),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """CU-37 — Audio → (Whisper) → texto → filtros del reporte.

    No genera el archivo: devuelve la transcripción + los filtros interpretados
    para que el frontend muestre la pantalla de confirmación antes de descargar.
    """
    data = await audio.read()
    if not data:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Audio vacío.",
        )
    if len(data) > _MAX_AUDIO_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="El audio supera el límite de 25 MB.",
        )
    try:
        return await report_voice_service.transcribe_and_interpret(
            db,
            tenant_id=current_user.tenant_id,
            audio_bytes=data,
            filename=audio.filename or "audio.webm",
        )
    except DomainValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)
        )
