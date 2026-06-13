"""Storage service — wrapper de boto3. Único punto que conoce S3."""

from uuid import uuid4

from app.core.config import settings

ALLOWED_MIME_TYPES = {
    "image/jpeg",
    "image/png",
    "image/gif",
    "image/webp",
    "video/mp4",
    "video/quicktime",
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/zip",
    "text/plain",
}

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB

EVIDENCE_TYPES = {
    "photo":       {"allowed_mimes": {"image/jpeg", "image/png", "image/gif", "image/webp"}},
    "video":       {"allowed_mimes": {"video/mp4", "video/quicktime"}},
    "invoice":     {"allowed_mimes": {"application/pdf", "image/jpeg", "image/png"}},
    "technical_report": {"allowed_mimes": {"application/pdf", "image/jpeg", "image/png"}},
    "sketch":      {"allowed_mimes": {"image/jpeg", "image/png", "application/pdf"}},
    "police_report":   {"allowed_mimes": {"application/pdf", "image/jpeg", "image/png"}},
    "personal_doc":    {"allowed_mimes": {"image/jpeg", "image/png", "application/pdf"}},
    "other":       {"allowed_mimes": ALLOWED_MIME_TYPES},
}


def _build_s3_key(subject_type: str, subject_id: str, file_name: str) -> str:
    safe_name = file_name.replace(" ", "_")
    return f"{subject_type}/{subject_id}/{uuid4().hex}_{safe_name}"


class StorageService:
    """Wrapper around boto3 S3 client for presigned URLs and bucket ops.

    boto3 is lazy-imported so the app can start without it for tests
    that don't touch S3 endpoints (document_requests, traffic_reports).

    Uses TWO clients so dev with LocalStack works:
    - internal client (AWS_S3_ENDPOINT): server-side ops from inside the
      compose network (e.g. http://localstack:4566).
    - public client (AWS_S3_PUBLIC_ENDPOINT or AWS_S3_ENDPOINT): only used to
      sign presigned URLs that the browser will follow (e.g. http://localhost:4566).
      Never makes network calls — `generate_presigned_url` just builds a string.
    In production both endpoints are the same; AWS_S3_PUBLIC_ENDPOINT stays None.
    """

    def __init__(self) -> None:
        self._client = None         # internal: head_bucket, head_object, create_bucket
        self._public_client = None  # public: generate_presigned_url only
        self._bucket = settings.AWS_S3_BUCKET

    def _ensure_client(self):
        if self._client is None:
            import boto3
            from botocore.config import Config as BotoConfig
            common_config = BotoConfig(
                signature_version="s3v4",
                s3={"addressing_style": "path"},
            )
            self._client = boto3.client(
                "s3",
                region_name=settings.AWS_REGION,
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                endpoint_url=settings.AWS_S3_ENDPOINT,
                config=common_config,
            )
            public_endpoint = settings.AWS_S3_PUBLIC_ENDPOINT or settings.AWS_S3_ENDPOINT
            self._public_client = boto3.client(
                "s3",
                region_name=settings.AWS_REGION,
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                endpoint_url=public_endpoint,
                config=common_config,
            )

    async def ensure_bucket(self) -> None:
        self._ensure_client()
        try:
            self._client.head_bucket(Bucket=self._bucket)
        except Exception:
            self._client.create_bucket(Bucket=self._bucket)
        # Configure bucket CORS so browsers can PUT directly via presigned URLs.
        # Idempotent — put_bucket_cors overwrites existing rules.
        self._client.put_bucket_cors(
            Bucket=self._bucket,
            CORSConfiguration={
                "CORSRules": [
                    {
                        "AllowedHeaders": ["*"],
                        "AllowedMethods": ["PUT", "GET", "POST", "DELETE", "HEAD"],
                        "AllowedOrigins": list(settings.CORS_ORIGINS),
                        "ExposeHeaders": ["ETag"],
                        "MaxAgeSeconds": 3000,
                    }
                ]
            },
        )

    def generate_presigned_upload(
        self,
        *,
        subject_type: str,
        subject_id: str,
        file_name: str,
        mime_type: str,
        file_size: int,
        evidence_type: str,
        expiration: int = 600,
    ) -> tuple[str, str]:
        """Returns (presigned_url, s3_key). Validates type/mime/size before generating."""
        self._ensure_client()

        if file_size > MAX_FILE_SIZE:
            raise ValueError(f"El archivo supera el tamaño máximo de {MAX_FILE_SIZE // 1024 // 1024} MB")

        if mime_type not in ALLOWED_MIME_TYPES:
            raise ValueError(f"Tipo MIME no permitido: {mime_type}")

        type_info = EVIDENCE_TYPES.get(evidence_type, EVIDENCE_TYPES["other"])
        if mime_type not in type_info["allowed_mimes"]:
            raise ValueError(
                f"El tipo MIME '{mime_type}' no es compatible con el tipo de evidencia '{evidence_type}'"
            )

        s3_key = _build_s3_key(subject_type, str(subject_id), file_name)

        url = self._public_client.generate_presigned_url(
            ClientMethod="put_object",
            Params={
                "Bucket": self._bucket,
                "Key": s3_key,
                "ContentType": mime_type,
            },
            ExpiresIn=expiration,
        )
        return url, s3_key

    def generate_presigned_download(self, s3_key: str, expiration: int = 3600) -> str:
        self._ensure_client()
        return self._public_client.generate_presigned_url(
            ClientMethod="get_object",
            Params={
                "Bucket": self._bucket,
                "Key": s3_key,
            },
            ExpiresIn=expiration,
        )

    def object_exists(self, s3_key: str) -> bool:
        self._ensure_client()
        try:
            self._client.head_object(Bucket=self._bucket, Key=s3_key)
            return True
        except Exception:
            return False

    def get_object_metadata(self, s3_key: str) -> dict | None:
        self._ensure_client()
        try:
            return self._client.head_object(Bucket=self._bucket, Key=s3_key)
        except Exception:
            return None

    def get_object_bytes(self, s3_key: str) -> bytes:
        """Descarga el objeto completo (server-side). Usado por DamageVisionService
        para mandar la imagen a OpenAI Vision como base64 — la URL presignada de
        LocalStack no es alcanzable desde afuera, los bytes sí."""
        self._ensure_client()
        obj = self._client.get_object(Bucket=self._bucket, Key=s3_key)
        return obj["Body"].read()


storage_service = StorageService()
