"""Canal asegurado — endpoints `/api/me/*` (CU-02..CU-08).

Todos requieren un JWT con ``scope='insured'`` (via ``get_current_account``).
Aislamiento estricto por cuenta: las solicitudes y expedientes se filtran por la
cuenta / policyholder del asegurado autenticado. Cross-account devuelve 404.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies import get_current_account
from app.models.claim_request import ClaimRequestStatus
from app.models.policyholder_account import PolicyholderAccount
from app.schemas.claim import (
    ClaimOutInsured,
    InsuredClaimRequestListItem,
    InsuredClaimRequestListResponse,
    InsuredDocumentRequestOut,
    InsuredTimelineEntry,
    PolicyholderSnippet,
    PolicySnippet,
    PublicObservationOut,
    VehicleSnippet,
)
from app.schemas.ai_analysis import AIAnalysisOut
from app.schemas.claim_request import (
    ClaimRequestCreate,
    ClaimRequestOut,
    ClaimRequestUpdate,
)
from app.schemas.evidence import (
    EvidenceListResponse,
    EvidenceOut,
    InsuredEvidenceRegister,
    InsuredPresignRequest,
    PresignedUrlResponse,
)
from app.schemas.policy import PolicyOut
from app.schemas.vehicle import VehicleOut
from app.services.claim_request_service import ClaimRequestService
from app.services.claim_service import ClaimService
from app.services.document_request_service import document_request_service
from app.services.evidence_service import evidence_service
from app.services.exceptions import (
    ConflictError,
    NotFoundError,
    PermissionError,
    ValidationError,
)
from app.services.policy_service import PolicyService
from app.services.storage_service import storage_service
from app.services.vehicle_service import VehicleService

router = APIRouter(prefix="/me", tags=["insured-channel"])
claim_request_service = ClaimRequestService()
claim_service = ClaimService()
policy_service = PolicyService()
vehicle_service = VehicleService()


# ── Catálogo del asegurado (para el wizard CU-02 paso 1) ──────────────


@router.get("/policies", response_model=list[PolicyOut])
async def list_my_policies(
    account: PolicyholderAccount = Depends(get_current_account),
    db: AsyncSession = Depends(get_db),
):
    items, _ = await policy_service.list_policies(
        db,
        tenant_id=account.tenant_id,
        policyholder_id=account.policyholder_id,
        page=1,
        limit=100,
    )
    return [PolicyOut.model_validate(p) for p in items]


@router.get("/vehicles", response_model=list[VehicleOut])
async def list_my_vehicles(
    account: PolicyholderAccount = Depends(get_current_account),
    db: AsyncSession = Depends(get_db),
):
    items = await vehicle_service.list_for_policyholder(
        db, tenant_id=account.tenant_id, policyholder_id=account.policyholder_id
    )
    return [VehicleOut.model_validate(v) for v in items]


def _raise(exc: Exception) -> None:
    if isinstance(exc, NotFoundError):
        raise HTTPException(status_code=404, detail=str(exc))
    if isinstance(exc, ConflictError):
        raise HTTPException(status_code=409, detail=str(exc))
    if isinstance(exc, ValidationError):
        raise HTTPException(status_code=422, detail=str(exc))
    if isinstance(exc, PermissionError):
        raise HTTPException(status_code=403, detail=str(exc))
    raise exc


# ── Solicitudes (CU-02/03/05/06) ──────────────────────────────────────


@router.get("/claim-requests", response_model=InsuredClaimRequestListResponse)
async def list_my_claim_requests(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    account: PolicyholderAccount = Depends(get_current_account),
    db: AsyncSession = Depends(get_db),
):
    items, total = await claim_request_service.list_for_account(
        db,
        tenant_id=account.tenant_id,
        account_id=account.id,
        page=page,
        limit=limit,
    )
    return InsuredClaimRequestListResponse(
        items=[InsuredClaimRequestListItem.model_validate(r) for r in items],
        total=total,
        page=page,
        limit=limit,
    )


@router.post(
    "/claim-requests",
    response_model=ClaimRequestOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_my_draft(
    body: ClaimRequestCreate,
    account: PolicyholderAccount = Depends(get_current_account),
    db: AsyncSession = Depends(get_db),
):
    try:
        # Seguridad: el asegurado solo puede crear solicitudes para SU propio
        # policyholder, sin importar lo que mande el cliente.
        cr = await claim_request_service.create_draft(
            db,
            tenant_id=account.tenant_id,
            policyholder_id=account.policyholder_id,
            policy_id=body.policy_id,
            vehicle_id=body.vehicle_id,
            accident_date=body.accident_date,
            accident_time=body.accident_time,
            accident_location=body.accident_location,
            accident_lat=body.accident_lat,
            accident_lng=body.accident_lng,
            accident_description=body.accident_description,
            reported_damages=body.reported_damages,
            created_by_account_id=account.id,
        )
        await db.commit()
        return ClaimRequestOut.model_validate(cr)
    except (NotFoundError, ValidationError) as e:
        await db.rollback()
        _raise(e)


@router.get("/claim-requests/{request_id}", response_model=ClaimRequestOut)
async def get_my_claim_request(
    request_id: UUID,
    account: PolicyholderAccount = Depends(get_current_account),
    db: AsyncSession = Depends(get_db),
):
    try:
        cr = await claim_request_service.get_for_account(
            db, request_id=request_id, tenant_id=account.tenant_id, account_id=account.id
        )
        return ClaimRequestOut.model_validate(cr)
    except NotFoundError as e:
        _raise(e)


@router.patch("/claim-requests/{request_id}", response_model=ClaimRequestOut)
async def update_my_draft(
    request_id: UUID,
    body: ClaimRequestUpdate,
    account: PolicyholderAccount = Depends(get_current_account),
    db: AsyncSession = Depends(get_db),
):
    try:
        # El asegurado no puede reasignar la solicitud a otro policyholder.
        fields = body.model_dump(exclude_unset=True)
        fields.pop("policyholder_id", None)
        cr = await claim_request_service.update_draft(
            db,
            request_id=request_id,
            tenant_id=account.tenant_id,
            account_id=account.id,
            fields=fields,
        )
        await db.commit()
        return ClaimRequestOut.model_validate(cr)
    except (NotFoundError, ConflictError, ValidationError) as e:
        await db.rollback()
        _raise(e)


@router.delete("/claim-requests/{request_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_my_draft(
    request_id: UUID,
    account: PolicyholderAccount = Depends(get_current_account),
    db: AsyncSession = Depends(get_db),
):
    try:
        await claim_request_service.delete_draft(
            db, request_id=request_id, tenant_id=account.tenant_id, account_id=account.id
        )
        await db.commit()
    except (NotFoundError, ConflictError) as e:
        await db.rollback()
        _raise(e)


@router.post("/claim-requests/{request_id}/submit", response_model=ClaimRequestOut)
async def submit_my_claim_request(
    request_id: UUID,
    account: PolicyholderAccount = Depends(get_current_account),
    db: AsyncSession = Depends(get_db),
):
    try:
        cr = await claim_request_service.submit(
            db, request_id=request_id, tenant_id=account.tenant_id, account_id=account.id
        )
        await db.commit()
        return ClaimRequestOut.model_validate(cr)
    except (NotFoundError, ConflictError, ValidationError) as e:
        await db.rollback()
        _raise(e)


# ── Evidencias del asegurado (CU-04) ──────────────────────────────────


@router.post(
    "/claim-requests/{request_id}/evidences/presign",
    response_model=PresignedUrlResponse,
)
async def presign_my_evidence(
    request_id: UUID,
    payload: InsuredPresignRequest,
    account: PolicyholderAccount = Depends(get_current_account),
    db: AsyncSession = Depends(get_db),
):
    try:
        # Verifica propiedad + que la solicitud es del asegurado.
        await claim_request_service.get_for_account(
            db, request_id=request_id, tenant_id=account.tenant_id, account_id=account.id
        )
        url, s3_key = await evidence_service.create_presigned_upload(
            subject_type="claim_request",
            subject_id=request_id,
            file_name=payload.file_name,
            mime_type=payload.mime_type,
            file_size=payload.file_size,
            evidence_type=payload.type,
            tenant_id=account.tenant_id,
        )
        return PresignedUrlResponse(upload_url=url, s3_key=s3_key)
    except (NotFoundError, ValidationError) as e:
        _raise(e)


@router.post(
    "/claim-requests/{request_id}/evidences",
    response_model=EvidenceOut,
    status_code=status.HTTP_201_CREATED,
)
async def register_my_evidence(
    request_id: UUID,
    payload: InsuredEvidenceRegister,
    account: PolicyholderAccount = Depends(get_current_account),
    db: AsyncSession = Depends(get_db),
):
    try:
        # Verifica propiedad antes de asociar la evidencia.
        await claim_request_service.get_for_account(
            db, request_id=request_id, tenant_id=account.tenant_id, account_id=account.id
        )
        evidence = await evidence_service.register_uploaded(
            db,
            subject_type="claim_request",
            subject_id=request_id,
            s3_key=payload.s3_key,
            evidence_type=payload.type,
            file_name=payload.file_name,
            mime_type=payload.mime_type,
            file_size=payload.file_size,
            metadata=payload.metadata,
            document_request_id=payload.document_request_id,
            tenant_id=account.tenant_id,
            actor_account_id=account.id,
        )
        await db.commit()
        out = EvidenceOut.model_validate(evidence)
        try:
            out.download_url = storage_service.generate_presigned_download(
                evidence.file_url
            )
        except Exception:
            out.download_url = None
        return out
    except (NotFoundError, ConflictError, ValidationError) as e:
        await db.rollback()
        _raise(e)


# ── CU-33 (Ciclo 8): análisis de daño por foto — OpenAI Vision server-side ──


@router.post(
    "/claim-requests/{request_id}/evidences/{evidence_id}/analyze-damage",
    response_model=AIAnalysisOut,
)
async def analyze_my_evidence_damage(
    request_id: UUID,
    evidence_id: UUID,
    account: PolicyholderAccount = Depends(get_current_account),
    db: AsyncSession = Depends(get_db),
):
    """El asegurado pide el análisis de la foto del daño. La API key de
    OpenAI vive solo en el backend (ADR-012); la app nunca la conoce.
    Si Vision falla, devuelve el análisis con status='error' (F-A1) para
    que la app ofrezca reintentar."""
    try:
        # Propiedad de la solicitud (cross-account → 404).
        cr = await claim_request_service.get_for_account(
            db, request_id=request_id, tenant_id=account.tenant_id, account_id=account.id
        )
        # La evidencia debe pertenecer a ESA solicitud y al tenant.
        from sqlalchemy import select as sa_select

        from app.models.evidence import Evidence

        evidence = (
            await db.execute(
                sa_select(Evidence).where(
                    Evidence.id == evidence_id,
                    Evidence.claim_request_id == request_id,
                    Evidence.tenant_id == account.tenant_id,
                )
            )
        ).scalar_one_or_none()
        if evidence is None:
            raise NotFoundError("Evidencia no encontrada")

        from app.services.ai.damage_vision_service import damage_vision_service

        analysis = await damage_vision_service.analyze_evidence(
            db, tenant_id=account.tenant_id, claim_request=cr, evidence=evidence
        )
        await db.commit()
        return AIAnalysisOut.model_validate(analysis)
    except (NotFoundError, ValidationError) as e:
        await db.rollback()
        _raise(e)


@router.get(
    "/claim-requests/{request_id}/evidences", response_model=EvidenceListResponse
)
async def list_my_request_evidences(
    request_id: UUID,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    account: PolicyholderAccount = Depends(get_current_account),
    db: AsyncSession = Depends(get_db),
):
    try:
        await claim_request_service.get_for_account(
            db, request_id=request_id, tenant_id=account.tenant_id, account_id=account.id
        )
    except NotFoundError as e:
        _raise(e)
    items, total = await evidence_service.list_for_subject(
        db,
        tenant_id=account.tenant_id,
        subject_type="claim_request",
        subject_id=request_id,
        page=page,
        limit=limit,
    )
    out_items = []
    for ev in items:
        o = EvidenceOut.model_validate(ev)
        try:
            o.download_url = storage_service.generate_presigned_download(ev.file_url)
        except Exception:
            o.download_url = None
        out_items.append(o)
    return EvidenceListResponse(items=out_items, total=total, page=page, limit=limit)


# ── Expediente formalizado (CU-06) ────────────────────────────────────


@router.get("/claims/{claim_id}", response_model=ClaimOutInsured)
async def get_my_claim(
    claim_id: UUID,
    account: PolicyholderAccount = Depends(get_current_account),
    db: AsyncSession = Depends(get_db),
):
    try:
        data = await claim_service.get_for_insured(
            db,
            claim_id=claim_id,
            tenant_id=account.tenant_id,
            policyholder_id=account.policyholder_id,
        )
    except NotFoundError as e:
        _raise(e)

    claim = data["claim"]
    out = ClaimOutInsured.model_validate(claim)
    out.policyholder = (
        PolicyholderSnippet.model_validate(data["policyholder"])
        if data["policyholder"]
        else None
    )
    out.policy = (
        PolicySnippet.model_validate(data["policy"]) if data["policy"] else None
    )
    out.vehicle = (
        VehicleSnippet.model_validate(data["vehicle"]) if data["vehicle"] else None
    )
    out.observations = [
        PublicObservationOut.model_validate(o) for o in data["observations"]
    ]
    out.document_requests = [
        InsuredDocumentRequestOut.model_validate(d) for d in data["document_requests"]
    ]
    out.timeline = [InsuredTimelineEntry(**t) for t in data["timeline"]]
    return out


# ── Documentación solicitada (CU-08) ──────────────────────────────────


@router.post(
    "/document-requests/{doc_request_id}/evidences/presign",
    response_model=PresignedUrlResponse,
)
async def presign_document_evidence(
    doc_request_id: UUID,
    payload: InsuredPresignRequest,
    account: PolicyholderAccount = Depends(get_current_account),
    db: AsyncSession = Depends(get_db),
):
    """Presign para subir documentación solicitada (CU-08). El subject es el claim
    del document_request, validado contra el policyholder del asegurado."""
    try:
        dr = await document_request_service.get_for_insured(
            db,
            doc_request_id=doc_request_id,
            tenant_id=account.tenant_id,
            policyholder_id=account.policyholder_id,
        )
        url, s3_key = await evidence_service.create_presigned_upload(
            subject_type="claim",
            subject_id=dr.claim_id,
            file_name=payload.file_name,
            mime_type=payload.mime_type,
            file_size=payload.file_size,
            evidence_type=payload.type,
            tenant_id=account.tenant_id,
        )
        return PresignedUrlResponse(upload_url=url, s3_key=s3_key)
    except (NotFoundError, ValidationError) as e:
        _raise(e)


@router.post(
    "/document-requests/{doc_request_id}/evidences",
    response_model=EvidenceOut,
    status_code=status.HTTP_201_CREATED,
)
async def submit_document(
    doc_request_id: UUID,
    payload: InsuredEvidenceRegister,
    account: PolicyholderAccount = Depends(get_current_account),
    db: AsyncSession = Depends(get_db),
):
    """El asegurado adjunta un documento solicitado y se cierra el pedido (CU-08).

    El subject de la evidencia es el expediente (claim) asociado al document_request.
    Tras registrar la evidencia, se marca el document_request como ``submitted``
    (que puede auto-transicionar el claim de docs_pending → in_review).
    """
    try:
        dr = await document_request_service.get_for_insured(
            db,
            doc_request_id=doc_request_id,
            tenant_id=account.tenant_id,
            policyholder_id=account.policyholder_id,
        )
        evidence = await evidence_service.register_uploaded(
            db,
            subject_type="claim",
            subject_id=dr.claim_id,
            s3_key=payload.s3_key,
            evidence_type=payload.type,
            file_name=payload.file_name,
            mime_type=payload.mime_type,
            file_size=payload.file_size,
            metadata=payload.metadata,
            document_request_id=doc_request_id,
            tenant_id=account.tenant_id,
            actor_account_id=account.id,
        )
        await document_request_service.submit_by_account(
            db,
            request_id=doc_request_id,
            tenant_id=account.tenant_id,
            account_id=account.id,
        )
        await db.commit()
        out = EvidenceOut.model_validate(evidence)
        try:
            out.download_url = storage_service.generate_presigned_download(
                evidence.file_url
            )
        except Exception:
            out.download_url = None
        return out
    except (NotFoundError, ConflictError, ValidationError) as e:
        await db.rollback()
        _raise(e)


# Nota: las notificaciones del asegurado (CU-06/CU-27) se sirven desde el router
# compartido `/api/me/notifications` (app/routers/notifications.py), que despacha
# según el scope del token vía get_current_principal. No se duplican acá.
