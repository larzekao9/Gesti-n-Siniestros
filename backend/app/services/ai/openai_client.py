"""Cliente OpenAI compartido. Único punto que conoce la API key.

La key vive en settings (backend). El frontend y la app móvil NUNCA la ven:
el móvil consume CU-33 vía endpoint propio (`DamageVisionService`).
"""

from app.core.config import settings
from app.services.exceptions import ValidationError

_client = None


def get_openai_client():
    """Devuelve un AsyncOpenAI lazy. Falla con error de dominio si falta la key."""
    global _client
    if not settings.OPENAI_API_KEY:
        raise ValidationError(
            "OPENAI_API_KEY no configurada — agregala al .env de la raíz"
        )
    if _client is None:
        from openai import AsyncOpenAI

        _client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    return _client


def reset_client_cache() -> None:
    """Para tests: descarta el cliente cacheado."""
    global _client
    _client = None
