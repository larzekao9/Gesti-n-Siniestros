"""Workflow state machine service for claim_requests and claims."""

from uuid import UUID

from app.models.claim import ClaimStatus
from app.models.claim_request import ClaimRequestStatus
from app.services.exceptions import InvalidStateTransitionError, ValidationError


class WorkflowService:
    """State machines for claim_requests and claims."""

    # ── claim_request state machine ──────────────────────────────
    _CLAIM_REQUEST_TRANSITIONS: dict[ClaimRequestStatus, set[ClaimRequestStatus]] = {
        ClaimRequestStatus.DRAFT: {ClaimRequestStatus.SUBMITTED},
        ClaimRequestStatus.SUBMITTED: {ClaimRequestStatus.UNDER_INTAKE_REVIEW},
        ClaimRequestStatus.UNDER_INTAKE_REVIEW: {
            ClaimRequestStatus.FORMALIZED,
            ClaimRequestStatus.REJECTED_AT_INTAKE,
        },
        # Terminal states — no outgoing transitions
        ClaimRequestStatus.FORMALIZED: set(),
        ClaimRequestStatus.REJECTED_AT_INTAKE: set(),
    }

    # Allow reopening from rejected back to submitted (admin only)
    _CLAIM_REQUEST_ADMIN_TRANSITIONS: dict[ClaimRequestStatus, set[ClaimRequestStatus]] = {
        ClaimRequestStatus.REJECTED_AT_INTAKE: {ClaimRequestStatus.SUBMITTED},
    }

    # ── claim state machine ──────────────────────────────────────
    # Full definition from CONTEXT.md; docs_pending gated by document_requests existence (Ciclo 4)
    _CLAIM_TRANSITIONS: dict[ClaimStatus, set[ClaimStatus]] = {
        ClaimStatus.REGISTERED: {ClaimStatus.IN_REVIEW},
        ClaimStatus.IN_REVIEW: {
            ClaimStatus.OBSERVED,
            ClaimStatus.IN_EVALUATION,
            # docs_pending gated — see transition_claim
        },
        ClaimStatus.OBSERVED: {
            ClaimStatus.IN_REVIEW,
            ClaimStatus.IN_EVALUATION,
            # docs_pending gated — see transition_claim
        },
        # docs_pending -> in_review handled automatically when all docs completed (Ciclo 4)
        ClaimStatus.DOCS_PENDING: {ClaimStatus.IN_REVIEW},
        ClaimStatus.IN_EVALUATION: {ClaimStatus.APPROVED, ClaimStatus.REJECTED},
        ClaimStatus.APPROVED: {ClaimStatus.CLOSED},
        ClaimStatus.REJECTED: {ClaimStatus.CLOSED},
        ClaimStatus.CLOSED: set(),
    }

    # Admin-only reopen transitions
    _CLAIM_ADMIN_TRANSITIONS: dict[ClaimStatus, set[ClaimStatus]] = {
        ClaimStatus.CLOSED: {ClaimStatus.IN_REVIEW},
        ClaimStatus.APPROVED: {ClaimStatus.IN_REVIEW},
        ClaimStatus.REJECTED: {ClaimStatus.IN_REVIEW},
    }

    # ── claim request methods ────────────────────────────────────

    def validate_transition(
        self,
        *,
        current: ClaimRequestStatus,
        target: ClaimRequestStatus,
        is_admin: bool = False,
    ) -> None:
        allowed = self._CLAIM_REQUEST_TRANSITIONS.get(current, set())

        if is_admin:
            admin_allowed = self._CLAIM_REQUEST_ADMIN_TRANSITIONS.get(current, set())
            allowed = allowed | admin_allowed

        if target not in allowed:
            raise InvalidStateTransitionError(
                f"No se puede pasar de '{current.value}' a '{target.value}'"
            )

    def allowed_targets(
        self, current: ClaimRequestStatus, *, is_admin: bool = False
    ) -> list[ClaimRequestStatus]:
        allowed = self._CLAIM_REQUEST_TRANSITIONS.get(current, set())
        if is_admin:
            allowed = allowed | self._CLAIM_REQUEST_ADMIN_TRANSITIONS.get(current, set())
        return sorted(allowed, key=lambda s: s.value)

    # ── claim methods ────────────────────────────────────────────

    def validate_claim_transition(
        self,
        *,
        current: ClaimStatus,
        target: ClaimStatus,
        is_admin: bool = False,
        has_document_requests: bool = False,
    ) -> None:
        allowed = self._CLAIM_TRANSITIONS.get(current, set())

        # Gate the docs_pending transition: only allowed when document_requests exist (Ciclo 4)
        if (
            current in (ClaimStatus.IN_REVIEW, ClaimStatus.OBSERVED)
            and target == ClaimStatus.DOCS_PENDING
            and not has_document_requests
        ):
            raise InvalidStateTransitionError(
                "La transición a 'docs_pending' requiere al menos una solicitud de documentación creada "
                "(funcionalidad disponible en Ciclo 4)"
            )

        if is_admin:
            admin_allowed = self._CLAIM_ADMIN_TRANSITIONS.get(current, set())
            allowed = allowed | admin_allowed

        if target not in allowed:
            raise InvalidStateTransitionError(
                f"No se puede pasar de '{current.value}' a '{target.value}'"
            )

    def allowed_claim_targets(
        self, current: ClaimStatus, *, is_admin: bool = False, has_document_requests: bool = False
    ) -> list[ClaimStatus]:
        allowed = self._CLAIM_TRANSITIONS.get(current, set())
        if is_admin:
            allowed = allowed | self._CLAIM_ADMIN_TRANSITIONS.get(current, set())
        # Filter out docs_pending if no document_requests exist
        if not has_document_requests and ClaimStatus.DOCS_PENDING in allowed:
            allowed = allowed - {ClaimStatus.DOCS_PENDING}
        return sorted(allowed, key=lambda s: s.value)

    # Transiciones donde el motivo es obligatorio (auditoría / justificación).
    # Mantener sincronizado con la constante REASON_REQUIRED en el frontend.
    _REASON_REQUIRED_PAIRS: frozenset[tuple[ClaimStatus, ClaimStatus]] = frozenset({
        # Marcar observado exige describir qué se observó.
        (ClaimStatus.IN_REVIEW, ClaimStatus.OBSERVED),
        # Decisiones finales requieren justificación.
        (ClaimStatus.IN_EVALUATION, ClaimStatus.APPROVED),
        (ClaimStatus.IN_EVALUATION, ClaimStatus.REJECTED),
    })

    @staticmethod
    def transitions_require_reason(current: ClaimStatus, target: ClaimStatus) -> bool:
        """Whether a reason is required for this transition."""
        return (current, target) in WorkflowService._REASON_REQUIRED_PAIRS
