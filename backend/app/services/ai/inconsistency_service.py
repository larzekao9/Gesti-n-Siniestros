"""InconsistencyAnalysisService — LLM que compara declaración vs póliza vs
vehículo vs documentos OCR (CU-32, contrato `inconsistency`).

Contrato del payload (Context.md §6 Ciclo 8):
    {"findings": [{"severity": "info|warning|critical", "field", "message"}]}
"""

import json

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.services.ai.claim_context import (
    ClaimContext,
    damage_severities,
    ocr_fragments,
)
from app.services.ai.openai_client import get_openai_client

_VALID_SEVERITIES = {"info", "warning", "critical"}

_SYSTEM_PROMPT = """Sos un analista experto en siniestros vehiculares de una aseguradora.
Tu tarea es detectar INCONSISTENCIAS entre la declaración del asegurado, los datos
de la póliza, el vehículo y los documentos adjuntos (texto OCR).

Buscá específicamente:
- Fechas: accidente fuera de la vigencia de la póliza, o contradicciones de fecha entre declaración y documentos.
- Cobertura: daños declarados que las exclusiones de la póliza no cubren.
- Vehículo: placa/marca/modelo del documento OCR que no coinciden con el vehículo asegurado.
- Relato: contradicciones internas en la descripción (lugar, hora, mecánica del choque vs daños).
- Severidad: la severidad del daño estimada por la app del asegurado (si está disponible) que contradice fuerte los daños declarados (ej. estima «Severo» pero se declaró un raspón menor, o estima «Leve» pero se declara una pérdida total).

Respondé SOLO un JSON válido con esta forma exacta:
{"findings": [{"severity": "info"|"warning"|"critical", "field": "<campo afectado>", "message": "<explicación breve en español>"}]}
Si no hay inconsistencias, devolvé {"findings": []}.
NO inventes hallazgos: solo reportá lo que surja de los datos provistos."""


def _build_user_prompt(ctx: ClaimContext) -> str:
    c = ctx.claim
    lines = [
        "## Declaración del siniestro",
        f"- Fecha del accidente: {c.accident_date}",
        f"- Hora: {c.accident_time or 'no informada'}",
        f"- Lugar: {c.accident_location}",
        f"- Descripción: {c.accident_description or 'sin descripción'}",
        f"- Daños reportados: {c.reported_damages or 'sin detalle'}",
    ]
    if ctx.policy:
        p = ctx.policy
        lines += [
            "## Póliza",
            f"- Número: {p.policy_number}",
            f"- Vigencia: {p.valid_from} a {p.valid_to}",
            f"- Cobertura: {p.coverage_type}",
            f"- Exclusiones: {p.exclusions or 'ninguna declarada'}",
        ]
    if ctx.vehicle:
        v = ctx.vehicle
        lines += [
            "## Vehículo asegurado",
            f"- Placa: {v.plate} | {v.make} {v.model} {v.year} | color {v.color or 'n/d'} | tipo {v.vehicle_type}",
        ]
    if ctx.policyholder:
        lines += ["## Asegurado", f"- {ctx.policyholder.full_name}"]

    fragments = ocr_fragments(ctx)
    if fragments:
        lines.append("## Texto OCR de documentos adjuntos (extraído por la app móvil)")
        for i, frag in enumerate(fragments, 1):
            lines.append(f"--- Documento {i} ---\n{frag}")
    else:
        lines.append("## Documentos adjuntos: sin texto OCR disponible")

    severities = damage_severities(ctx)
    if severities:
        lines.append(
            "## Severidad del daño estimada on-device por la app del asegurado "
            "(CU-35, advisory — modelo en el celular, NO definitiva)"
        )
        for i, s in enumerate(severities, 1):
            lines.append(
                f"- Foto {i}: severidad «{s['severidad']}» (confianza {s['confianza']:.0%})"
            )
        lines.append(
            "Si esta estimación contradice fuerte los «Daños reportados», reportá un "
            "finding de severity «warning» en field «daños/severidad». No la trates "
            "como verdad absoluta (el modelo se puede equivocar)."
        )

    evidence_types = [e.type.value for e in ctx.evidences]
    lines.append(f"## Evidencias adjuntas: {evidence_types or 'ninguna'}")
    return "\n".join(lines)


class InconsistencyAnalysisService:
    async def analyze(self, db: AsyncSession, *, ctx: ClaimContext) -> dict:
        client = get_openai_client()
        resp = await client.chat.completions.create(
            model=settings.OPENAI_CHAT_MODEL,
            response_format={"type": "json_object"},
            temperature=0.1,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": _build_user_prompt(ctx)},
            ],
        )
        raw = json.loads(resp.choices[0].message.content or "{}")

        findings = []
        for item in raw.get("findings", []):
            if not isinstance(item, dict):
                continue
            severity = str(item.get("severity", "info")).lower()
            findings.append(
                {
                    "severity": severity if severity in _VALID_SEVERITIES else "info",
                    "field": str(item.get("field", ""))[:120],
                    "message": str(item.get("message", ""))[:500],
                }
            )

        critical = sum(1 for f in findings if f["severity"] == "critical")
        warning = sum(1 for f in findings if f["severity"] == "warning")
        if not findings:
            explanation = "No se detectaron inconsistencias entre la declaración, la póliza y los documentos."
        else:
            explanation = (
                f"Se detectaron {len(findings)} inconsistencia(s): "
                f"{critical} crítica(s), {warning} advertencia(s)."
            )

        return {
            "score": None,
            "payload": {"findings": findings},
            "explanation": explanation,
        }


inconsistency_service = InconsistencyAnalysisService()
