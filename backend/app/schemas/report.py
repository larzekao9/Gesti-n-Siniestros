"""Schemas de reportes por voz — CU-37."""

from pydantic import BaseModel, Field


class ReportInterpretRequest(BaseModel):
    """Texto ya transcripto (fallback / tests sin audio)."""

    text: str = Field(min_length=1, max_length=1000)


class VoiceReportFilters(BaseModel):
    """Filtros listos para alimentar `GET /api/reports/claims`."""

    format: str = "pdf"
    status: str | None = None
    from_: str | None = Field(default=None, alias="from")
    to: str | None = None
    analyst: str | None = None
    supervisor: str | None = None
    policyholder: str | None = None
    q: str | None = None

    model_config = {"populate_by_name": True}


class VoiceReportResolved(BaseModel):
    """Etiquetas legibles para la pantalla de confirmación."""

    format: str
    status_label: str | None = None
    analyst_label: str | None = None
    supervisor_label: str | None = None
    policyholder_label: str | None = None


class VoiceReportInterpretation(BaseModel):
    """Resultado de interpretar un pedido de reporte (texto o voz)."""

    transcript: str
    supported: bool
    note: str = ""
    filters: VoiceReportFilters
    resolved: VoiceReportResolved
    warnings: list[str] = []
