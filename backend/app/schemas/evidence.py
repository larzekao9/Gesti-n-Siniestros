"""Evidence Pydantic schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class PresignedUrlRequest(BaseModel):
    subject_type: str = Field(..., description="'claim' o 'claim_request'")
    subject_id: UUID
    type: str = Field(..., description="Tipo de evidencia: photo, video, invoice, etc.")
    file_name: str
    mime_type: str
    file_size: int = Field(..., gt=0, le=52428800)


class PresignedUrlResponse(BaseModel):
    upload_url: str
    s3_key: str
    expires_in: int = 600


class EvidenceRegister(BaseModel):
    subject_type: str = Field(..., description="'claim' o 'claim_request'")
    subject_id: UUID
    s3_key: str
    type: str
    file_name: str
    mime_type: str
    file_size: int
    metadata: dict | None = None
    document_request_id: UUID | None = None


class EvidenceOut(BaseModel):
    # `metadata` collides with SQLAlchemy's reserved `MetaData` registry on the
    # declarative class. The ORM column is mapped via the Python attribute
    # `metadata_`, so we read from that alias and still serialize as `metadata`
    # in the JSON output (which is what the frontend expects).
    model_config = {"from_attributes": True, "populate_by_name": True}

    id: UUID
    tenant_id: UUID
    claim_request_id: UUID | None = None
    claim_id: UUID | None = None
    type: str
    file_url: str
    # Presigned GET URL ready for the browser. Populated server-side by the
    # router so thumbnails/downloads in the gallery work without an extra
    # round-trip per item. Short-lived (≈1h) — the FE can re-fetch via
    # /api/evidences/{id}/download for fresh links if needed.
    download_url: str | None = None
    file_name: str
    mime_type: str
    file_size: int
    metadata: dict | None = Field(default=None, validation_alias="metadata_")
    uploaded_by_user_id: UUID | None = None
    document_request_id: UUID | None = None
    created_at: datetime
    updated_at: datetime | None = None


class InsuredPresignRequest(BaseModel):
    """Presign desde el canal asegurado — el subject es el claim_request del path."""

    type: str = Field(..., description="Tipo de evidencia: photo, video, etc.")
    file_name: str
    mime_type: str
    file_size: int = Field(..., gt=0, le=52428800)


class InsuredEvidenceRegister(BaseModel):
    """Registro de evidencia del asegurado — subject implícito (claim_request del path)."""

    s3_key: str
    type: str
    file_name: str
    mime_type: str
    file_size: int
    metadata: dict | None = None
    document_request_id: UUID | None = None


class EvidenceDownloadUrlResponse(BaseModel):
    download_url: str
    expires_in: int = 3600


class EvidenceListResponse(BaseModel):
    items: list[EvidenceOut]
    total: int
    page: int
    limit: int
