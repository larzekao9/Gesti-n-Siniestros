"""Document request domain service — CU-07, CU-08."""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.claim import Claim, ClaimStatus
from app.models.document_request import DocumentRequest, DocumentRequestStatus
from app.models.notification import NotificationKind
from app.models.policyholder_account import PolicyholderAccount
from app.services.audit_service import AuditService
from app.services.exceptions import ConflictError, NotFoundError
from app.services.notification_service import notification_service

audit_service = AuditService()


class DocumentRequestService:
    """Manages document requests from analyst to insured."""

    async def create(
        self,
        db: AsyncSession,
        *,
        claim_id: UUID,
        description: str,
        tenant_id: UUID,
        actor_user_id: UUID,
    ) -> DocumentRequest:
        claim = await db.execute(
            select(Claim).where(Claim.id == claim_id, Claim.tenant_id == tenant_id)
        )
        claim = claim.scalar_one_or_none()
        if claim is None:
            raise NotFoundError("Expediente no encontrado")

        if claim.status == ClaimStatus.CLOSED:
            raise ConflictError("No se pueden solicitar documentos a un expediente cerrado")

        doc_req = DocumentRequest(
            tenant_id=tenant_id,
            claim_id=claim_id,
            requested_by_user_id=actor_user_id,
            description=description,
            status=DocumentRequestStatus.PENDING,
        )
        db.add(doc_req)
        await db.flush()

        await audit_service.write(
            db,
            tenant_id=tenant_id,
            action="CREATE_DOCUMENT_REQUEST",
            entity_type="document_request",
            entity_id=doc_req.id,
            actor_user_id=actor_user_id,
            payload_diff={"claim_id": str(claim_id), "description": description},
        )

        # Retro-enganche Ciclo 7: notificar al asegurado que se le pide documentación
        # (CU-07). Se busca la cuenta activa del policyholder del expediente. Si no
        # tiene cuenta (asegurado sin canal móvil), create() es no-op.
        account = await db.execute(
            select(PolicyholderAccount).where(
                PolicyholderAccount.policyholder_id == claim.policyholder_id,
                PolicyholderAccount.tenant_id == tenant_id,
                PolicyholderAccount.is_active == True,  # noqa: E712
            )
        )
        account = account.scalar_one_or_none()
        if account is not None:
            await notification_service.create(
                db,
                tenant_id=tenant_id,
                recipient_account_id=account.id,
                entity_type="document_request",
                entity_id=doc_req.id,
                kind=NotificationKind.DOCS_REQUESTED,
                title="Documentación solicitada",
                body=f"Se te solicitó documentación para tu expediente {claim.claim_number}: {description}",
            )

        await db.refresh(doc_req)
        return doc_req

    async def submit(
        self,
        db: AsyncSession,
        *,
        request_id: UUID,
        tenant_id: UUID,
        actor_user_id: UUID,
    ) -> DocumentRequest:
        dr = await db.execute(
            select(DocumentRequest).where(
                DocumentRequest.id == request_id, DocumentRequest.tenant_id == tenant_id
            )
        )
        dr = dr.scalar_one_or_none()
        if dr is None:
            raise NotFoundError("Solicitud de documentación no encontrada")

        if dr.status != DocumentRequestStatus.PENDING:
            raise ConflictError("La solicitud de documentación ya fue resuelta")

        from datetime import datetime, timezone
        dr.status = DocumentRequestStatus.SUBMITTED
        dr.resolved_at = datetime.now(timezone.utc)

        await audit_service.write(
            db,
            tenant_id=tenant_id,
            action="SUBMIT_DOCUMENT_REQUEST",
            entity_type="document_request",
            entity_id=dr.id,
            actor_user_id=actor_user_id,
        )

        await db.flush()
        await db.refresh(dr)

        # If all doc_requests for this claim are resolved, auto-transition back to in_review
        await self._auto_transition_if_all_resolved(
            db, claim_id=dr.claim_id, tenant_id=tenant_id, actor_user_id=actor_user_id
        )
        return dr

    async def get_for_insured(
        self,
        db: AsyncSession,
        *,
        doc_request_id: UUID,
        tenant_id: UUID,
        policyholder_id: UUID,
    ) -> DocumentRequest:
        """Carga un document_request verificando que el claim sea del asegurado (CU-08).

        Cross-account devuelve 404 (no filtra existencia).
        """
        result = await db.execute(
            select(DocumentRequest)
            .join(Claim, Claim.id == DocumentRequest.claim_id)
            .where(
                DocumentRequest.id == doc_request_id,
                DocumentRequest.tenant_id == tenant_id,
                Claim.policyholder_id == policyholder_id,
            )
        )
        dr = result.scalar_one_or_none()
        if dr is None:
            raise NotFoundError("Solicitud de documentación no encontrada")
        return dr

    async def submit_by_account(
        self,
        db: AsyncSession,
        *,
        request_id: UUID,
        tenant_id: UUID,
        account_id: UUID,
    ) -> DocumentRequest:
        """Cierra un document_request cuando el asegurado adjunta la documentación (CU-08)."""
        dr = await db.execute(
            select(DocumentRequest).where(
                DocumentRequest.id == request_id, DocumentRequest.tenant_id == tenant_id
            )
        )
        dr = dr.scalar_one_or_none()
        if dr is None:
            raise NotFoundError("Solicitud de documentación no encontrada")

        if dr.status != DocumentRequestStatus.PENDING:
            raise ConflictError("La solicitud de documentación ya fue resuelta")

        from datetime import datetime, timezone
        dr.status = DocumentRequestStatus.SUBMITTED
        dr.resolved_at = datetime.now(timezone.utc)

        await audit_service.write(
            db,
            tenant_id=tenant_id,
            action="SUBMIT_DOCUMENT_REQUEST",
            entity_type="document_request",
            entity_id=dr.id,
            actor_account_id=account_id,
        )

        await db.flush()
        await db.refresh(dr)

        # Auto-transición del claim si ya no quedan pedidos pendientes.
        await self._auto_transition_if_all_resolved(
            db, claim_id=dr.claim_id, tenant_id=tenant_id, actor_user_id=None
        )
        return dr

    async def waive(
        self,
        db: AsyncSession,
        *,
        request_id: UUID,
        tenant_id: UUID,
        actor_user_id: UUID,
    ) -> DocumentRequest:
        dr = await db.execute(
            select(DocumentRequest).where(
                DocumentRequest.id == request_id, DocumentRequest.tenant_id == tenant_id
            )
        )
        dr = dr.scalar_one_or_none()
        if dr is None:
            raise NotFoundError("Solicitud de documentación no encontrada")

        if dr.status != DocumentRequestStatus.PENDING:
            raise ConflictError("La solicitud de documentación ya fue resuelta")

        from datetime import datetime, timezone
        dr.status = DocumentRequestStatus.WAIVED
        dr.resolved_at = datetime.now(timezone.utc)

        await audit_service.write(
            db,
            tenant_id=tenant_id,
            action="WAIVE_DOCUMENT_REQUEST",
            entity_type="document_request",
            entity_id=dr.id,
            actor_user_id=actor_user_id,
        )

        await db.flush()
        await db.refresh(dr)

        await self._auto_transition_if_all_resolved(
            db, claim_id=dr.claim_id, tenant_id=tenant_id, actor_user_id=actor_user_id
        )
        return dr

    async def _auto_transition_if_all_resolved(
        self,
        db: AsyncSession,
        *,
        claim_id: UUID,
        tenant_id: UUID,
        actor_user_id: UUID,
    ) -> None:
        """If all document_requests for a claim are submitted/waived and claim is docs_pending,
        transition back to in_review."""
        from app.models.state_transition import StateTransition, SubjectType

        claim = await db.execute(
            select(Claim).where(Claim.id == claim_id, Claim.tenant_id == tenant_id)
        )
        claim = claim.scalar_one_or_none()
        if claim is None or claim.status != ClaimStatus.DOCS_PENDING:
            return

        # Check if any pending requests remain
        pending = await db.execute(
            select(func.count()).select_from(
                select(DocumentRequest).where(
                    DocumentRequest.claim_id == claim_id,
                    DocumentRequest.tenant_id == tenant_id,
                    DocumentRequest.status == DocumentRequestStatus.PENDING,
                ).subquery()
            )
        )
        if pending.scalar_one() > 0:
            return

        # All resolved → transition back
        old_status = claim.status
        claim.status = ClaimStatus.IN_REVIEW

        transition = StateTransition(
            tenant_id=tenant_id,
            subject_type=SubjectType.CLAIM,
            subject_id=claim.id,
            from_status=old_status.value,
            to_status=ClaimStatus.IN_REVIEW.value,
            reason="Todas las solicitudes de documentación completadas",
            actor_user_id=actor_user_id,
        )
        db.add(transition)

    async def list_for_claim(
        self,
        db: AsyncSession,
        *,
        claim_id: UUID,
        tenant_id: UUID,
        page: int = 1,
        limit: int = 20,
    ) -> tuple[list[DocumentRequest], int]:
        offset = (page - 1) * limit
        query = select(DocumentRequest).where(
            DocumentRequest.claim_id == claim_id, DocumentRequest.tenant_id == tenant_id
        )
        count_q = select(func.count()).select_from(query.subquery())
        total = (await db.execute(count_q)).scalar_one()

        query = query.order_by(DocumentRequest.created_at.desc()).offset(offset).limit(limit)
        result = await db.execute(query)
        return list(result.scalars().all()), total

    async def has_pending_requests(
        self, db: AsyncSession, *, claim_id: UUID, tenant_id: UUID
    ) -> bool:
        result = await db.execute(
            select(func.count()).select_from(
                select(DocumentRequest).where(
                    DocumentRequest.claim_id == claim_id,
                    DocumentRequest.tenant_id == tenant_id,
                    DocumentRequest.status == DocumentRequestStatus.PENDING,
                ).subquery()
            )
        )
        return result.scalar_one() > 0


document_request_service = DocumentRequestService()
