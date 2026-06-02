"""Document request router — CU-07, CU-08."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.document_request import (
    DocumentRequestCreate,
    DocumentRequestListResponse,
    DocumentRequestOut,
    DocumentRequestSubmit,
)
from app.services.document_request_service import document_request_service
from app.services.exceptions import (
    ConflictError,
    NotFoundError,
    ValidationError,
)

router = APIRouter(prefix="/document-requests", tags=["document_requests"])


@router.get("", response_model=DocumentRequestListResponse)
async def list_for_claim(
    claim_id: UUID = Query(..., alias="claim_id"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    items, total = await document_request_service.list_for_claim(
        db,
        claim_id=claim_id,
        tenant_id=current_user.tenant_id,
        page=page,
        limit=limit,
    )
    return DocumentRequestListResponse(
        items=[DocumentRequestOut.model_validate(d) for d in items],
        total=total,
        page=page,
        limit=limit,
    )


@router.post("", response_model=DocumentRequestOut, status_code=status.HTTP_201_CREATED)
async def create_document_request(
    payload: DocumentRequestCreate,
    claim_id: UUID = Query(..., alias="claim_id"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        dr = await document_request_service.create(
            db,
            claim_id=claim_id,
            description=payload.description,
            tenant_id=current_user.tenant_id,
            actor_user_id=current_user.id,
        )
        await db.commit()
        return DocumentRequestOut.model_validate(dr)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ConflictError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.post("/{request_id}/submit", response_model=DocumentRequestOut)
async def submit_document_request(
    request_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        dr = await document_request_service.submit(
            db,
            request_id=request_id,
            tenant_id=current_user.tenant_id,
            actor_user_id=current_user.id,
        )
        await db.commit()
        return DocumentRequestOut.model_validate(dr)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ConflictError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.post("/{request_id}/waive", response_model=DocumentRequestOut)
async def waive_document_request(
    request_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        dr = await document_request_service.waive(
            db,
            request_id=request_id,
            tenant_id=current_user.tenant_id,
            actor_user_id=current_user.id,
        )
        await db.commit()
        return DocumentRequestOut.model_validate(dr)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ConflictError as e:
        raise HTTPException(status_code=409, detail=str(e))
