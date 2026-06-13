"""Contexto compartido de un claim para los análisis IA.

Carga una sola vez todo lo que necesitan los tres análisis (inconsistencias,
duplicados, fraude): claim + póliza + vehículo + asegurado + evidencias
(con su ``ocr_text`` si la app móvil lo extrajo — CU-34) + historial.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.claim import Claim
from app.models.evidence import Evidence
from app.models.policy import Policy
from app.models.policyholder import Policyholder
from app.models.vehicle import Vehicle
from app.services.exceptions import NotFoundError

# Topes para no exceder el contexto del LLM ni el límite de embeddings.
_OCR_FRAGMENT_CAP = 600
_TEXT_TOTAL_CAP = 6000


@dataclass
class ClaimContext:
    claim: Claim
    policyholder: Policyholder | None
    policy: Policy | None
    vehicle: Vehicle | None
    evidences: list[Evidence]
    prior_claims_count: int  # mismos policyholder, último año, sin contar este


async def load_claim_context(
    db: AsyncSession, *, claim_id: UUID, tenant_id: UUID
) -> ClaimContext:
    claim = (
        await db.execute(
            select(Claim).where(Claim.id == claim_id, Claim.tenant_id == tenant_id)
        )
    ).scalar_one_or_none()
    if claim is None:
        raise NotFoundError("Expediente no encontrado")

    policyholder = await db.get(Policyholder, claim.policyholder_id)
    policy = await db.get(Policy, claim.policy_id)
    vehicle = await db.get(Vehicle, claim.vehicle_id)

    evidences = list(
        (
            await db.execute(
                select(Evidence).where(
                    Evidence.claim_id == claim_id, Evidence.tenant_id == tenant_id
                )
            )
        ).scalars()
    )

    a_year_ago = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=365)
    prior_claims_count = (
        await db.execute(
            select(func.count())
            .select_from(Claim)
            .where(
                Claim.tenant_id == tenant_id,
                Claim.policyholder_id == claim.policyholder_id,
                Claim.id != claim.id,
                Claim.created_at >= a_year_ago,
            )
        )
    ).scalar_one()

    return ClaimContext(
        claim=claim,
        policyholder=policyholder,
        policy=policy,
        vehicle=vehicle,
        evidences=evidences,
        prior_claims_count=prior_claims_count,
    )


def ocr_fragments(ctx: ClaimContext) -> list[str]:
    """Textos OCR extraídos on-device por la app móvil (CU-34), truncados."""
    fragments: list[str] = []
    for ev in ctx.evidences:
        meta = ev.metadata_ or {}
        text = meta.get("ocr_text")
        if text and isinstance(text, str) and text.strip():
            fragments.append(text.strip()[:_OCR_FRAGMENT_CAP])
    return fragments


def build_claim_text(ctx: ClaimContext) -> str:
    """Texto canónico del claim para embeddings (duplicados, ADR-011)."""
    c = ctx.claim
    parts = [
        f"Fecha del accidente: {c.accident_date}",
        f"Lugar: {c.accident_location}",
        f"Descripción: {c.accident_description or ''}",
        f"Daños reportados: {c.reported_damages or ''}",
    ]
    if ctx.vehicle:
        v = ctx.vehicle
        parts.append(f"Vehículo: {v.make} {v.model} {v.year} placa {v.plate}")
    parts.extend(ocr_fragments(ctx))
    return "\n".join(parts)[:_TEXT_TOTAL_CAP]
