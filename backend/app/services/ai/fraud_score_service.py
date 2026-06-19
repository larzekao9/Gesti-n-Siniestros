"""FraudScoreService — score de fraude heurístico explicable (ADR-010).

NO usa modelo entrenado ni SHAP: reglas expertas con pesos. Cada factor que
dispara queda en el payload con su contribución y dirección — esa lista ES
la explicación (reemplaza a SHAP). Contrato (Context.md §6 Ciclo 8):

    {"score": 0..1, "factors": [{"name", "contribution", "direction": "up"|"down"}]}

Baseline correcto para un sistema sin histórico de fraude etiquetado; cuando
se acumulen datos reales puede reemplazarse por un modelo sin tocar el
contrato del payload.
"""

from datetime import timedelta

from app.core.config import settings
from app.models.evidence import EvidenceType
from app.services.ai.claim_context import ClaimContext

_BASE_SCORE = 0.05


class FraudScoreService:
    """Cómputo puro (sin IO): recibe el contexto ya cargado."""

    def compute(
        self, *, ctx: ClaimContext, duplicate_top_similarity: float | None = None
    ) -> dict:
        c = ctx.claim
        factors: list[dict] = []

        def add(name: str, contribution: float) -> None:
            factors.append(
                {
                    "name": name,
                    "contribution": round(contribution, 4),
                    "direction": "up" if contribution > 0 else "down",
                }
            )

        # ── Factores que suben el riesgo ─────────────────────────────
        if c.accident_time is not None and 0 <= c.accident_time.hour < 6:
            add("Accidente en horario nocturno (00:00–05:59)", +0.15)

        if ctx.policy is not None and c.accident_date is not None:
            policy_age_days = (c.accident_date - ctx.policy.valid_from).days
            if 0 <= policy_age_days < 30:
                add("Póliza con menos de 30 días de antigüedad al accidente", +0.25)
            elif 30 <= policy_age_days < 90:
                add("Póliza con menos de 90 días de antigüedad al accidente", +0.12)

            days_to_expiry = (ctx.policy.valid_to - c.accident_date).days
            if 0 <= days_to_expiry <= 14:
                add("Accidente a ≤14 días del vencimiento de la póliza", +0.10)

        if c.accident_date is not None and c.created_at is not None:
            report_delay = (c.created_at.date() - c.accident_date).days
            if report_delay > 30:
                add("Demora mayor a 30 días en reportar el siniestro", +0.15)

        if ctx.prior_claims_count >= 2:
            add(
                f"Historial: {ctx.prior_claims_count} siniestros del asegurado en el último año",
                +0.20,
            )
        elif ctx.prior_claims_count == 1:
            add("Historial: 1 siniestro previo del asegurado en el último año", +0.10)

        if not ctx.evidences:
            add("Expediente sin evidencias adjuntas", +0.10)

        if (
            duplicate_top_similarity is not None
            and duplicate_top_similarity >= settings.AI_DUPLICATE_THRESHOLD
        ):
            add("Alta similitud con otro expediente (posible duplicado)", +0.20)

        # ── Factores que bajan el riesgo ─────────────────────────────
        if ctx.policy is not None and c.accident_date is not None:
            if (c.accident_date - ctx.policy.valid_from) >= timedelta(days=730):
                add("Póliza con 2+ años de antigüedad", -0.10)

        if any(e.type == EvidenceType.POLICE_REPORT for e in ctx.evidences):
            add("Incluye acta policial entre las evidencias", -0.10)

        if c.accident_lat is not None and c.accident_lng is not None:
            add("Reporte con coordenadas GPS del lugar del accidente", -0.05)

        raw = _BASE_SCORE + sum(f["contribution"] for f in factors)
        score = round(min(1.0, max(0.0, raw)), 4)

        ups = [f["name"] for f in factors if f["direction"] == "up"]
        downs = [f["name"] for f in factors if f["direction"] == "down"]
        parts = [f"Score de riesgo: {score:.2f}."]
        if ups:
            parts.append("Aumentan el riesgo: " + "; ".join(ups) + ".")
        if downs:
            parts.append("Disminuyen el riesgo: " + "; ".join(downs) + ".")
        if not factors:
            parts.append("Sin factores de riesgo relevantes detectados.")

        return {
            "score": score,
            "payload": {"score": score, "factors": factors},
            "explanation": " ".join(parts),
        }


fraud_score_service = FraudScoreService()
