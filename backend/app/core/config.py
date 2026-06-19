"""Application configuration via pydantic-settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables or .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/siniestros"
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7  # staff interno (web): sesión corta
    # Canal asegurado (app móvil): sesión larga estilo app de consumo — el
    # asegurado permanece logueado hasta que cierre sesión manualmente (que
    # revoca el refresh). Separado del staff a propósito (no extender al staff).
    INSURED_REFRESH_TOKEN_EXPIRE_DAYS: int = 365
    REDIS_URL: str = "redis://localhost:6379/0"
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]
    ENVIRONMENT: str = "development"

    # ── S3 / LocalStack ───────────────────────────────────────────
    AWS_ACCESS_KEY_ID: str = "test"
    AWS_SECRET_ACCESS_KEY: str = "test"
    AWS_REGION: str = "us-east-1"
    # Internal endpoint: used for server-side ops (head_bucket, create_bucket).
    # In docker: http://localstack:4566 (resolved inside compose network).
    AWS_S3_ENDPOINT: str = "http://localhost:4566"
    # Browser-facing endpoint: used to SIGN presigned URLs that the user's
    # browser will hit. In docker, the internal hostname `localstack` is not
    # resolvable from the host machine, so presigned URLs must use `localhost`.
    # Leave as None in production (same endpoint serves both roles).
    AWS_S3_PUBLIC_ENDPOINT: str | None = None
    AWS_S3_BUCKET: str = "siniestros-evidencias"

    # ── IA (Ciclo 8) ──────────────────────────────────────────────
    OPENAI_API_KEY: str = ""
    OPENAI_CHAT_MODEL: str = "gpt-4o-mini"
    OPENAI_VISION_MODEL: str = "gpt-4o-mini"
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"  # 1536 dims
    AI_DUPLICATE_THRESHOLD: float = 0.90
    AI_FRAUD_ALERT_THRESHOLD: float = 0.85


settings = Settings()
