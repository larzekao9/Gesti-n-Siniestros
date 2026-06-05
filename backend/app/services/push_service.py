"""Push notification dispatcher — Expo Push API (Ciclo 7, CU-27 canal asegurado).

Fire-and-forget: nunca rompe la transacción que lo invoca. Si no hay device
tokens, o la Expo Push API falla, se registra el error y se sigue. El envío real
se hace fuera de la transacción de negocio (best-effort).
"""

import logging
from uuid import UUID

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.device_token import DeviceToken

logger = logging.getLogger("uvicorn.error")

EXPO_PUSH_URL = "https://exp.host/--/api/v2/push/send"


class PushService:
    """Despacha push notifications a los dispositivos de un asegurado vía Expo."""

    async def send(
        self,
        db: AsyncSession,
        *,
        tenant_id: UUID,
        account_id: UUID,
        title: str,
        body: str,
        data: dict | None = None,
    ) -> int:
        """Envía un push a todos los dispositivos del asegurado. Best-effort.

        Returns:
            Número de dispositivos a los que se intentó enviar (0 si no hay).
            Nunca lanza: cualquier error se loguea y se devuelve el conteo.
        """
        try:
            result = await db.execute(
                select(DeviceToken).where(
                    DeviceToken.account_id == account_id,
                    DeviceToken.tenant_id == tenant_id,
                )
            )
            tokens = list(result.scalars().all())
        except Exception as exc:  # pragma: no cover - defensivo
            logger.warning("PushService: no se pudieron leer device_tokens (%s)", exc)
            return 0

        if not tokens:
            return 0

        messages = [
            {
                "to": t.expo_push_token,
                "title": title,
                "body": body,
                "data": data or {},
                "sound": "default",
            }
            for t in tokens
        ]

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.post(EXPO_PUSH_URL, json=messages)
                if resp.status_code >= 400:
                    logger.warning(
                        "PushService: Expo respondió %s — %s",
                        resp.status_code,
                        resp.text[:300],
                    )
        except Exception as exc:
            # Fire-and-forget: el fallo de push nunca debe afectar al negocio.
            logger.warning("PushService: fallo al enviar push (%s)", exc)

        return len(messages)


push_service = PushService()
