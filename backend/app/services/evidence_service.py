"""Evidence domain service — CU-04, CU-18."""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.claim import Claim
from app.models.claim_request import ClaimRequest
from app.models.evidence import Evidence, EvidenceType
from app.models.document_request import DocumentRequest
from app.services.audit_service import AuditService
from app.services.exceptions import ConflictError, NotFoundError, ValidationError
from app.services.storage_service import StorageService

audit_service = AuditService()
storage = StorageService()


class EvidenceService:
    """Manages evidence uploads and retrieval."""

    async def create_presigned_upload(
        self,
        *,
        subject_type: str,
        subject_id: UUID,
        file_name: str,
        mime_type: str,
        file_size: int,
        evidence_type: str,
        tenant_id: UUID,
    ) -> tuple[str, str]:
        """Validate permissions and generate presigned upload URL. Returns (url, s3_key)."""
        try:
            EvidenceType(evidence_type)
        except ValueError:
            raise ValidationError(f"Tipo de evidencia no válido: {evidence_type}")

        try:
            url, s3_key = storage.generate_presigned_upload(
                subject_type=subject_type,
                subject_id=str(subject_id),
                file_name=file_name,
                mime_type=mime_type,
                file_size=file_size,
                evidence_type=evidence_type,
            )
        except ValueError as e:
            raise ValidationError(str(e))

        return url, s3_key

    async def register_uploaded(
        self,
        db: AsyncSession,
        *,
        subject_type: str,
        subject_id: UUID,
        s3_key: str,
        evidence_type: str,
        file_name: str,
        mime_type: str,
        file_size: int,
        metadata: dict | None,
        document_request_id: UUID | None,
        tenant_id: UUID,
        actor_user_id: UUID | None = None,
        actor_account_id: UUID | None = None,
    ) -> Evidence:
        """Persist an evidence record after successful S3 upload.

        Soporta ambos canales: interno (``actor_user_id``) y asegurado
        (``actor_account_id``, Ciclo 7). Exactamente uno debe estar presente.
        """
        try:
            etype = EvidenceType(evidence_type)
        except ValueError:
            raise ValidationError(f"Tipo de evidencia no válido: {evidence_type}")

        # Validate subject exists and is not locked
        claim_request_id: UUID | None = None
        claim_id: UUID | None = None

        if subject_type == "claim_request":
            cr = await db.execute(
                select(ClaimRequest).where(
                    ClaimRequest.id == subject_id, ClaimRequest.tenant_id == tenant_id
                )
            )
            cr = cr.scalar_one_or_none()
            if cr is None:
                raise NotFoundError("Solicitud no encontrada")
            from app.models.claim_request import ClaimRequestStatus
            if cr.status in (ClaimRequestStatus.FORMALIZED, ClaimRequestStatus.REJECTED_AT_INTAKE):
                raise ConflictError("La solicitud está bloqueada y no acepta nuevas evidencias")
            claim_request_id = subject_id
        elif subject_type == "claim":
            c = await db.execute(
                select(Claim).where(Claim.id == subject_id, Claim.tenant_id == tenant_id)
            )
            c = c.scalar_one_or_none()
            if c is None:
                raise NotFoundError("Expediente no encontrado")
            if c.status == "closed":
                raise ConflictError("El expediente está cerrado y no acepta nuevas evidencias")
            claim_id = subject_id
        else:
            raise ValidationError(f"Tipo de sujeto no válido: {subject_type}")

        # Validate document_request if provided
        if document_request_id is not None:
            dr = await db.execute(
                select(DocumentRequest).where(
                    DocumentRequest.id == document_request_id,
                    DocumentRequest.tenant_id == tenant_id,
                )
            )
            dr = dr.scalar_one_or_none()
            if dr is None:
                raise NotFoundError("Solicitud de documentación no encontrada")
            if dr.status != "pending":
                raise ConflictError("La solicitud de documentación ya fue resuelta")

        evidence = Evidence(
            tenant_id=tenant_id,
            claim_request_id=claim_request_id,
            claim_id=claim_id,
            type=etype,
            file_url=s3_key,
            file_name=file_name,
            mime_type=mime_type,
            file_size=file_size,
            metadata_=metadata,
            uploaded_by_user_id=actor_user_id,
            uploaded_by_account_id=actor_account_id,
            document_request_id=document_request_id,
        )
        db.add(evidence)
        await db.flush()
        await db.refresh(evidence)

        await audit_service.write(
            db,
            tenant_id=tenant_id,
            action="UPLOAD_EVIDENCE",
            entity_type="evidence",
            entity_id=evidence.id,
            actor_user_id=actor_user_id,
            actor_account_id=actor_account_id,
            payload_diff={
                "subject_type": subject_type,
                "subject_id": str(subject_id),
                "type": evidence_type,
                "file_name": file_name,
            },
        )
        return evidence

    async def list_for_subject(
        self,
        db: AsyncSession,
        *,
        tenant_id: UUID,
        subject_type: str,
        subject_id: UUID,
        page: int = 1,
        limit: int = 20,
    ) -> tuple[list[Evidence], int]:
        offset = (page - 1) * limit
        query = select(Evidence).where(Evidence.tenant_id == tenant_id)

        if subject_type == "claim_request":
            query = query.where(Evidence.claim_request_id == subject_id)
        elif subject_type == "claim":
            query = query.where(Evidence.claim_id == subject_id)

        count_q = select(func.count()).select_from(query.subquery())
        total = (await db.execute(count_q)).scalar_one()

        query = query.order_by(Evidence.created_at.desc()).offset(offset).limit(limit)
        result = await db.execute(query)
        return list(result.scalars().all()), total

    async def get_download_url(
        self, db: AsyncSession, *, evidence_id: UUID, tenant_id: UUID
    ) -> str:
        result = await db.execute(
            select(Evidence).where(
                Evidence.id == evidence_id, Evidence.tenant_id == tenant_id
            )
        )
        ev = result.scalar_one_or_none()
        if ev is None:
            raise NotFoundError("Evidencia no encontrada")
        return storage.generate_presigned_download(ev.file_url)

    async def promote_request_evidences_to_claim(
        self,
        db: AsyncSession,
        *,
        claim_request_id: UUID,
        claim_id: UUID,
        tenant_id: UUID,
    ) -> int:
        """Add claim_id to all evidences that belong to a claim_request.
        Called during formalization (CU-10). Returns count of promoted evidences.
        """
        result = await db.execute(
            select(Evidence).where(
                Evidence.claim_request_id == claim_request_id,
                Evidence.tenant_id == tenant_id,
            )
        )
        evidences = result.scalars().all()
        for ev in evidences:
            ev.claim_id = claim_id
        await db.flush()
        return len(evidences)


evidence_service = EvidenceService()
