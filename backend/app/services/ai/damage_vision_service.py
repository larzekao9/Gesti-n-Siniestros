"""DamageVisionService — CU-33: análisis de daño por foto (ADR-012).

Corre SERVER-SIDE con OpenAI Vision: la app móvil llama al endpoint
`POST /api/me/claim-requests/{id}/evidences/{ev_id}/analyze-damage` y este
servicio es el único que toca la API key. La imagen se manda como base64
porque las URLs presignadas de LocalStack no son alcanzables desde OpenAI.

Contrato del payload: {"damage_type", "severity", "confidence"}.
"""

import base64
import json

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.ai_analysis import AIAnalysis, AIAnalysisKind, AIAnalysisStatus
from app.models.claim_request import ClaimRequest
from app.models.evidence import Evidence
from app.services.ai.openai_client import get_openai_client
from app.services.exceptions import ValidationError

_MAX_IMAGE_BYTES = 8 * 1024 * 1024  # límite razonable para base64 + vision
_VALID_SEVERITIES = {"leve", "moderado", "severo", "indeterminado"}

_SYSTEM_PROMPT = """Sos un perito vehicular. Analizá la foto del daño de un vehículo.
Respondé SOLO un JSON válido:
{"damage_type": "<tipo de daño en español, ej. 'colisión trasera', 'rayadura lateral'>",
 "severity": "leve"|"moderado"|"severo"|"indeterminado",
 "confidence": <0.0 a 1.0>,
 "explanation": "<1-2 frases en español describiendo lo que se ve>"}
Si la imagen no muestra un vehículo dañado, devolvé severity "indeterminado" y confidence baja."""


class DamageVisionService:
    async def analyze_evidence(
        self,
        db: AsyncSession,
        *,
        tenant_id,
        claim_request: ClaimRequest,
        evidence: Evidence,
    ) -> AIAnalysis:
        if not evidence.mime_type.startswith("image/"):
            raise ValidationError("Solo se pueden analizar evidencias de tipo imagen")
        if evidence.file_size > _MAX_IMAGE_BYTES:
            raise ValidationError("La imagen supera el tamaño máximo analizable (8 MB)")

        analysis = AIAnalysis(
            tenant_id=tenant_id,
            claim_request_id=claim_request.id,
            evidence_id=evidence.id,
            kind=AIAnalysisKind.DAMAGE_ASSESSMENT,
            status=AIAnalysisStatus.PROCESSING,
            model_version=settings.OPENAI_VISION_MODEL,
        )
        db.add(analysis)
        await db.flush()

        try:
            from app.services.storage_service import storage_service

            image_bytes = storage_service.get_object_bytes(evidence.file_url)
            b64 = base64.b64encode(image_bytes).decode("ascii")
            data_url = f"data:{evidence.mime_type};base64,{b64}"

            client = get_openai_client()
            resp = await client.chat.completions.create(
                model=settings.OPENAI_VISION_MODEL,
                response_format={"type": "json_object"},
                temperature=0.1,
                messages=[
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "Analizá el daño visible en esta foto del siniestro.",
                            },
                            {"type": "image_url", "image_url": {"url": data_url}},
                        ],
                    },
                ],
            )
            parsed = json.loads(resp.choices[0].message.content or "{}")

            severity = str(parsed.get("severity", "indeterminado")).lower()
            if severity not in _VALID_SEVERITIES:
                severity = "indeterminado"
            try:
                confidence = min(1.0, max(0.0, float(parsed.get("confidence", 0))))
            except (TypeError, ValueError):
                confidence = 0.0

            analysis.payload = {
                "damage_type": str(parsed.get("damage_type", "indeterminado"))[:120],
                "severity": severity,
                "confidence": round(confidence, 4),
            }
            analysis.score = round(confidence, 4)
            analysis.explanation = str(
                parsed.get("explanation", "Análisis de daño completado.")
            )[:500]
            analysis.status = AIAnalysisStatus.DONE
        except Exception as e:  # F-A1: Vision falló → status=error, la app reintenta
            analysis.status = AIAnalysisStatus.ERROR
            analysis.explanation = "No se pudo analizar la imagen. Intentá de nuevo."
            analysis.payload = {"error": str(e)[:300]}

        await db.flush()
        await db.refresh(analysis)
        return analysis


damage_vision_service = DamageVisionService()
