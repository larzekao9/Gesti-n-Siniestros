"""Celery tasks for post-processing uploaded evidence."""

from app.core.celery_app import celery_app
from app.services.audit_service import AuditService

audit_service = AuditService()


@celery_app.task(name="evidence_post_processing")
def evidence_post_processing(evidence_id: str) -> dict:
    """Post-process an uploaded evidence: record basic metadata, mime sniffing.
    
    Stub for now. TODO: EXIF extraction, thumbnail generation, OCR (future iterations).
    """
    # In a full async setting we would use asyncio, but Celery tasks are sync.
    # We keep this as a stub that logs the event.
    celery_app.log.info(f"evidence_post_processing started for evidence_id={evidence_id}")
    
    # TODO: async DB access from Celery requires an async runner or sync session.
    # For the stub, we just log that the task was triggered.
    
    celery_app.log.info(f"evidence_post_processing completed for evidence_id={evidence_id}")
    return {"status": "ok", "evidence_id": evidence_id}
