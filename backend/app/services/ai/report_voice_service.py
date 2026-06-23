"""ReportVoiceService — CU-37: generación de reportes operativos por voz.

Pipeline en tres pasos, todos server-side (la API key nunca sale del backend):

    audio ──Whisper──▶ texto ──LLM (JSON estricto)──▶ intención
                                                          │
                                  resolución contra el catálogo real del tenant
                                                          ▼
                                       filtros válidos del reporte CU-22

El LLM **no ejecuta nada**: solo traduce lenguaje libre al conjunto **cerrado**
de perillas que el endpoint `/api/reports/claims` ya acepta (formato, estado,
rango de fechas, analista, supervisor, asegurado, texto libre). Si el usuario
pide algo fuera de ese universo, `supported=False` y se devuelve una nota
explicando qué sí se puede pedir. Los nombres propios (analista, supervisor,
asegurado) se resuelven contra la base; si no hay match, queda un warning para
que el frontend lo muestre antes de generar.
"""

import json
import unicodedata
from datetime import date
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.policyholder import Policyholder
from app.models.user import Role, User
from app.services.ai.openai_client import get_openai_client

# Estados válidos del expediente (deben coincidir con la state machine de claims).
_STATUS_LABELS = {
    "registered": "Registrado",
    "in_review": "En revisión",
    "observed": "Observado",
    "docs_pending": "Docs. pendientes",
    "in_evaluation": "En evaluación",
    "approved": "Aprobado",
    "rejected": "Rechazado",
    "closed": "Cerrado",
}
_VALID_STATUSES = set(_STATUS_LABELS)
_VALID_FORMATS = {"pdf", "xlsx"}

_SYSTEM_PROMPT = """Sos un asistente que traduce pedidos de reportes hablados en
español al ÚNICO reporte que el sistema puede generar: el "Reporte operativo de
siniestros" de una aseguradora. Ese reporte solo admite estos filtros y NADA más:

- format: "pdf" o "xlsx" (formato del archivo). Si no lo dicen, dejá null.
- status: el estado del expediente. SOLO uno de estos valores exactos:
  registered, in_review, observed, docs_pending, in_evaluation, approved, rejected, closed.
  Mapeá el lenguaje natural: "aprobados"→approved, "rechazados"→rejected,
  "en revisión"→in_review, "observados"→observed, "en evaluación"→in_evaluation,
  "registrados/nuevos"→registered, "documentación pendiente"→docs_pending,
  "cerrados"→closed. Si no mencionan estado, null.
- date_from / date_to: rango de fechas del siniestro en formato YYYY-MM-DD.
  Resolvé expresiones relativas usando la FECHA DE HOY que te paso. Ejemplos:
  "este mes"→del día 1 al último del mes actual; "junio"→01 al 30 de junio del
  año actual; "los últimos 7 días"→hoy menos 7 días hasta hoy; "este año"→01-01
  al 31-12. Si no mencionan fechas, ambos null.
- analyst_name: nombre del analista si lo mencionan ("los de Juan Pérez",
  "del analista García"). Solo el nombre tal como se dijo. Si no, null.
- supervisor_name: nombre del supervisor si lo mencionan. Si no, null.
- policyholder_name: nombre del asegurado/cliente si lo mencionan. Si no, null.
- q: texto libre para buscar por placa de vehículo, número de expediente o lugar
  del accidente (ej. "la placa ABC-123", "el expediente EXP-2026-000004",
  "los de la avenida Busch"). Si no aplica, null.

Reglas:
- Si el pedido encaja en este reporte (aunque sea parcialmente), supported=true.
- Si piden un reporte que NO existe (ej. "reporte de fraude por color de auto",
  "ranking de productividad", "gráfico de torta", "exportar a Word", un dato que
  no es de siniestros), supported=false y explicá en "note" qué SÍ se puede pedir.
- NO inventes filtros que no se mencionaron. Ante la duda, dejá null.

Respondé SOLO un JSON válido con esta forma exacta:
{"supported": true|false, "format": null|"pdf"|"xlsx", "status": null|"<estado>",
 "date_from": null|"YYYY-MM-DD", "date_to": null|"YYYY-MM-DD",
 "analyst_name": null|"<nombre>", "supervisor_name": null|"<nombre>",
 "policyholder_name": null|"<nombre>", "q": null|"<texto>", "note": "<aclaración breve>"}"""


class ReportVoiceService:
    """Transcribe audio (Whisper) e interpreta el pedido como filtros del reporte."""

    async def transcribe(self, *, audio_bytes: bytes, filename: str) -> str:
        """Audio → texto vía Whisper. Devuelve la transcripción en español."""
        client = get_openai_client()
        resp = await client.audio.transcriptions.create(
            model=settings.OPENAI_TRANSCRIBE_MODEL,
            file=(filename, audio_bytes),
            language="es",
        )
        return (resp.text or "").strip()

    async def interpret(
        self, db: AsyncSession, *, tenant_id: UUID, text: str
    ) -> dict:
        """Texto → filtros válidos del reporte, resueltos contra el tenant.

        Devuelve un dict listo para el frontend: la transcripción, si el pedido
        es soportado, los filtros que alimentan `/api/reports/claims`, etiquetas
        legibles para la pantalla de confirmación y warnings de resolución.
        """
        raw = await self._llm_intent(text)

        supported = bool(raw.get("supported", False))
        note = str(raw.get("note", ""))[:400]
        warnings: list[str] = []

        # ── formato ──────────────────────────────────────────────────
        fmt = raw.get("format")
        report_format = fmt if fmt in _VALID_FORMATS else "pdf"

        # ── estado ───────────────────────────────────────────────────
        status_val = raw.get("status")
        status = status_val if status_val in _VALID_STATUSES else None
        if status_val and status is None:
            warnings.append(f"Estado «{status_val}» no reconocido; se ignoró.")

        # ── fechas ───────────────────────────────────────────────────
        date_from = self._parse_date(raw.get("date_from"))
        date_to = self._parse_date(raw.get("date_to"))

        # ── nombres → IDs (resueltos contra la base) ─────────────────
        analyst_id, analyst_label = await self._resolve_user(
            db, tenant_id=tenant_id, name=raw.get("analyst_name"), role=Role.ANALYST
        )
        if raw.get("analyst_name") and analyst_id is None:
            warnings.append(
                f"No se encontró un analista que coincida con «{raw['analyst_name']}»."
            )
        supervisor_id, supervisor_label = await self._resolve_user(
            db, tenant_id=tenant_id, name=raw.get("supervisor_name"), role=Role.SUPERVISOR
        )
        if raw.get("supervisor_name") and supervisor_id is None:
            warnings.append(
                f"No se encontró un supervisor que coincida con «{raw['supervisor_name']}»."
            )
        policyholder_id, policyholder_label = await self._resolve_policyholder(
            db, tenant_id=tenant_id, name=raw.get("policyholder_name")
        )
        if raw.get("policyholder_name") and policyholder_id is None:
            warnings.append(
                f"No se encontró un asegurado que coincida con «{raw['policyholder_name']}»."
            )

        q = (raw.get("q") or None)
        if q:
            q = str(q)[:120]

        return {
            "transcript": text,
            "supported": supported,
            "note": note,
            "filters": {
                "format": report_format,
                "status": status,
                "from": date_from.isoformat() if date_from else None,
                "to": date_to.isoformat() if date_to else None,
                "analyst": str(analyst_id) if analyst_id else None,
                "supervisor": str(supervisor_id) if supervisor_id else None,
                "policyholder": str(policyholder_id) if policyholder_id else None,
                "q": q,
            },
            "resolved": {
                "format": report_format,
                "status_label": _STATUS_LABELS.get(status) if status else None,
                "analyst_label": analyst_label,
                "supervisor_label": supervisor_label,
                "policyholder_label": policyholder_label,
            },
            "warnings": warnings,
        }

    async def transcribe_and_interpret(
        self, db: AsyncSession, *, tenant_id: UUID, audio_bytes: bytes, filename: str
    ) -> dict:
        """Atajo: audio → (Whisper) → texto → (LLM) → filtros."""
        text = await self.transcribe(audio_bytes=audio_bytes, filename=filename)
        return await self.interpret(db, tenant_id=tenant_id, text=text)

    # ── internos ─────────────────────────────────────────────────────

    async def _llm_intent(self, text: str) -> dict:
        client = get_openai_client()
        today = date.today().isoformat()
        resp = await client.chat.completions.create(
            model=settings.OPENAI_CHAT_MODEL,
            response_format={"type": "json_object"},
            temperature=0,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": f"FECHA DE HOY: {today}\nPedido del usuario: «{text}»",
                },
            ],
        )
        try:
            return json.loads(resp.choices[0].message.content or "{}")
        except (json.JSONDecodeError, TypeError):
            return {"supported": False, "note": "No se pudo interpretar el pedido."}

    @staticmethod
    def _parse_date(value) -> date | None:
        if not value or not isinstance(value, str):
            return None
        try:
            return date.fromisoformat(value[:10])
        except ValueError:
            return None

    @staticmethod
    def _normalize(value: str) -> str:
        """Minúsculas + sin acentos, para matchear nombres dictados por voz.

        La transcripción/LLM suele perder tildes («Juan Perez» vs «Juan Pérez»),
        así que el match contra la base debe ser insensible a acentos.
        """
        folded = unicodedata.normalize("NFKD", value)
        folded = "".join(c for c in folded if not unicodedata.combining(c))
        return folded.lower().strip()

    def _best_match(
        self, name: str, candidates: list[tuple[UUID, str]]
    ) -> tuple[UUID | None, str | None]:
        target = self._normalize(name)
        if not target:
            return None, None
        for cid, full_name in candidates:
            if target in self._normalize(full_name) or self._normalize(full_name) in target:
                return cid, full_name
        return None, None

    async def _resolve_user(
        self, db: AsyncSession, *, tenant_id: UUID, name, role: Role
    ) -> tuple[UUID | None, str | None]:
        if not name or not isinstance(name, str):
            return None, None
        res = await db.execute(
            select(User.id, User.full_name).where(
                User.tenant_id == tenant_id,
                User.role == role,
                User.is_active.is_(True),
            )
        )
        return self._best_match(name, list(res.all()))

    async def _resolve_policyholder(
        self, db: AsyncSession, *, tenant_id: UUID, name
    ) -> tuple[UUID | None, str | None]:
        if not name or not isinstance(name, str):
            return None, None
        res = await db.execute(
            select(Policyholder.id, Policyholder.full_name).where(
                Policyholder.tenant_id == tenant_id,
            )
        )
        return self._best_match(name, list(res.all()))


report_voice_service = ReportVoiceService()
