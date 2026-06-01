"""Tests for Cycle 3: WorkflowService state machines."""

import pytest
from app.services.workflow_service import WorkflowService
from app.services.exceptions import InvalidStateTransitionError
from app.models.claim import ClaimStatus
from app.models.claim_request import ClaimRequestStatus


@pytest.fixture
def wf() -> WorkflowService:
    return WorkflowService()


# ─── Claim Request state machine ────────────────────────────────────


def test_valid_claim_request_transitions(wf):
    wf.validate_transition(
        current=ClaimRequestStatus.DRAFT,
        target=ClaimRequestStatus.SUBMITTED,
    )
    wf.validate_transition(
        current=ClaimRequestStatus.SUBMITTED,
        target=ClaimRequestStatus.UNDER_INTAKE_REVIEW,
    )
    wf.validate_transition(
        current=ClaimRequestStatus.UNDER_INTAKE_REVIEW,
        target=ClaimRequestStatus.FORMALIZED,
    )
    wf.validate_transition(
        current=ClaimRequestStatus.UNDER_INTAKE_REVIEW,
        target=ClaimRequestStatus.REJECTED_AT_INTAKE,
    )


def test_invalid_claim_request_transition(wf):
    with pytest.raises(InvalidStateTransitionError):
        wf.validate_transition(
            current=ClaimRequestStatus.SUBMITTED,
            target=ClaimRequestStatus.DRAFT,
        )


# ─── Claim state machine ────────────────────────────────────────────


def test_valid_claim_transitions(wf):
    wf.validate_claim_transition(
        current=ClaimStatus.REGISTERED,
        target=ClaimStatus.IN_REVIEW,
    )
    wf.validate_claim_transition(
        current=ClaimStatus.IN_REVIEW,
        target=ClaimStatus.OBSERVED,
    )
    wf.validate_claim_transition(
        current=ClaimStatus.IN_REVIEW,
        target=ClaimStatus.IN_EVALUATION,
    )


def test_invalid_claim_transition(wf):
    with pytest.raises(InvalidStateTransitionError):
        wf.validate_claim_transition(
            current=ClaimStatus.REGISTERED,
            target=ClaimStatus.CLOSED,
        )


def test_docs_pending_gated(wf):
    with pytest.raises(InvalidStateTransitionError):
        wf.validate_claim_transition(
            current=ClaimStatus.IN_REVIEW,
            target=ClaimStatus.DOCS_PENDING,
            has_document_requests=False,
        )


def test_claim_terminal_states(wf):
    wf.validate_claim_transition(
        current=ClaimStatus.APPROVED,
        target=ClaimStatus.CLOSED,
    )
    wf.validate_claim_transition(
        current=ClaimStatus.REJECTED,
        target=ClaimStatus.CLOSED,
    )
    with pytest.raises(InvalidStateTransitionError):
        wf.validate_claim_transition(
            current=ClaimStatus.CLOSED,
            target=ClaimStatus.IN_REVIEW,
        )
    with pytest.raises(InvalidStateTransitionError):
        wf.validate_claim_transition(
            current=ClaimStatus.CLOSED,
            target=ClaimStatus.APPROVED,
        )
