"""Evidence router — CU-04, CU-18."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.evidence import (
    EvidenceDownloadUrlResponse,
    EvidenceListResponse,
    EvidenceOut,
    EvidenceRegister,
    PresignedUrlRequest,
    PresignedUrlResponse,
)
from app.services.evidence_service import evidence_service
from app.services.exceptions import (
    ConflictError,
    NotFoundError,
    ValidationError,
)
from app.services.storage_service import storage_service

router = APIRouter(prefix="/evidences", tags=["evidences"])


def _evidence_to_out(ev) -> EvidenceOut:
    """Serialize an Evidence ORM instance into EvidenceOut + populate the
    browser-facing presigned download URL so the FE can render thumbnails
    directly without an extra round-trip per item."""
    out = EvidenceOut.model_validate(ev)
    try:
        out.download_url = storage_service.generate_presigned_download(ev.file_url)
    except Exception:
        # Storage temporarily unreachable — return the row without a URL;
        # the FE can fall back to /api/evidences/{id}/download.
        out.download_url = None
    return out


@router.post("/presign", response_model=PresignedUrlResponse)
async def create_presigned_upload(
    payload: PresignedUrlRequest,
    current_user: User = Depends(get_current_user),
):
    try:
        url, s3_key = await evidence_service.create_presigned_upload(
            subject_type=payload.subject_type,
            subject_id=payload.subject_id,
            file_name=payload.file_name,
            mime_type=payload.mime_type,
            file_size=payload.file_size,
            evidence_type=payload.type,
            tenant_id=current_user.tenant_id,
        )
        return PresignedUrlResponse(upload_url=url, s3_key=s3_key)
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.post("", response_model=EvidenceOut, status_code=status.HTTP_201_CREATED)
async def register_evidence(
    payload: EvidenceRegister,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        evidence = await evidence_service.register_uploaded(
            db,
            subject_type=payload.subject_type,
            subject_id=payload.subject_id,
            s3_key=payload.s3_key,
            evidence_type=payload.type,
            file_name=payload.file_name,
            mime_type=payload.mime_type,
            file_size=payload.file_size,
            metadata=payload.metadata,
            document_request_id=payload.document_request_id,
            tenant_id=current_user.tenant_id,
            actor_user_id=current_user.id,
        )
        await db.commit()
        return _evidence_to_out(evidence)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ConflictError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.get("/claims/{claim_id}", response_model=EvidenceListResponse)
async def list_claim_evidences(
    claim_id: UUID,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    items, total = await evidence_service.list_for_subject(
        db,
        tenant_id=current_user.tenant_id,
        subject_type="claim",
        subject_id=claim_id,
        page=page,
        limit=limit,
    )
    return EvidenceListResponse(
        items=[_evidence_to_out(e) for e in items],
        total=total,
        page=page,
        limit=limit,
    )


@router.get("/claim-requests/{request_id}", response_model=EvidenceListResponse)
async def list_request_evidences(
    request_id: UUID,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    items, total = await evidence_service.list_for_subject(
        db,
        tenant_id=current_user.tenant_id,
        subject_type="claim_request",
        subject_id=request_id,
        page=page,
        limit=limit,
    )
    return EvidenceListResponse(
        items=[_evidence_to_out(e) for e in items],
        total=total,
        page=page,
        limit=limit,
    )


@router.get("/{evidence_id}/download", response_model=EvidenceDownloadUrlResponse)
async def get_download_url(
    evidence_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        url = await evidence_service.get_download_url(
            db, evidence_id=evidence_id, tenant_id=current_user.tenant_id
        )
        return EvidenceDownloadUrlResponse(download_url=url)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
