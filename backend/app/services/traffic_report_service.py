"""Traffic report domain service — CU-16."""

from datetime import date
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.claim import Claim
from app.models.traffic_report import TrafficReport
from app.services.audit_service import AuditService
from app.services.exceptions import NotFoundError, ValidationError

audit_service = AuditService()


class TrafficReportService:
    """Manages traffic / police report data for a claim."""

    async def create(
        self,
        db: AsyncSession,
        *,
        claim_id: UUID,
        evidence_id: UUID | None,
        officer_name: str | None,
        report_code: str | None,
        jurisdiction: str | None,
        report_date: date | None,
        summary: str | None,
        tenant_id: UUID,
        actor_user_id: UUID,
    ) -> TrafficReport:
        claim = await db.execute(
            select(Claim).where(Claim.id == claim_id, Claim.tenant_id == tenant_id)
        )
        if claim.scalar_one_or_none() is None:
            raise NotFoundError("Expediente no encontrado")

        # Validate evidence belongs to the claim if provided
        if evidence_id is not None:
            from app.models.evidence import Evidence
            ev = await db.execute(
                select(Evidence).where(
                    Evidence.id == evidence_id,
                    Evidence.tenant_id == tenant_id,
                    Evidence.claim_id == claim_id,
                )
            )
            if ev.scalar_one_or_none() is None:
                raise ValidationError("La evidencia no pertenece a este expediente")

        report = TrafficReport(
            tenant_id=tenant_id,
            claim_id=claim_id,
            evidence_id=evidence_id,
            officer_name=officer_name,
            report_code=report_code,
            jurisdiction=jurisdiction,
            report_date=report_date,
            summary=summary,
        )
        db.add(report)
        await db.flush()
        await db.refresh(report)

        await audit_service.write(
            db,
            tenant_id=tenant_id,
            action="CREATE_TRAFFIC_REPORT",
            entity_type="traffic_report",
            entity_id=report.id,
            actor_user_id=actor_user_id,
            payload_diff={"claim_id": str(claim_id)},
        )
        return report

    async def update(
        self,
        db: AsyncSession,
        *,
        report_id: UUID,
        evidence_id: UUID | None,
        officer_name: str | None,
        report_code: str | None,
        jurisdiction: str | None,
        report_date: date | None,
        summary: str | None,
        tenant_id: UUID,
        actor_user_id: UUID,
    ) -> TrafficReport:
        result = await db.execute(
            select(TrafficReport).where(
                TrafficReport.id == report_id, TrafficReport.tenant_id == tenant_id
            )
        )
        report = result.scalar_one_or_none()
        if report is None:
            raise NotFoundError("Informe de tránsito no encontrado")

        if evidence_id is not None:
            from app.models.evidence import Evidence
            ev = await db.execute(
                select(Evidence).where(
                    Evidence.id == evidence_id,
                    Evidence.tenant_id == tenant_id,
                    Evidence.claim_id == report.claim_id,
                )
            )
            if ev.scalar_one_or_none() is None:
                raise ValidationError("La evidencia no pertenece a este expediente")

        report.evidence_id = evidence_id if evidence_id is not None else report.evidence_id
        report.officer_name = officer_name if officer_name is not None else report.officer_name
        report.report_code = report_code if report_code is not None else report.report_code
        report.jurisdiction = jurisdiction if jurisdiction is not None else report.jurisdiction
        report.report_date = report_date if report_date is not None else report.report_date
        report.summary = summary if summary is not None else report.summary

        await db.flush()
        await db.refresh(report)

        await audit_service.write(
            db,
            tenant_id=tenant_id,
            action="UPDATE_TRAFFIC_REPORT",
            entity_type="traffic_report",
            entity_id=report.id,
            actor_user_id=actor_user_id,
        )
        return report

    async def delete(
        self,
        db: AsyncSession,
        *,
        report_id: UUID,
        tenant_id: UUID,
        actor_user_id: UUID,
    ) -> None:
        result = await db.execute(
            select(TrafficReport).where(
                TrafficReport.id == report_id, TrafficReport.tenant_id == tenant_id
            )
        )
        report = result.scalar_one_or_none()
        if report is None:
            raise NotFoundError("Informe de tránsito no encontrado")

        claim_id = report.claim_id
        await db.delete(report)

        await audit_service.write(
            db,
            tenant_id=tenant_id,
            action="DELETE_TRAFFIC_REPORT",
            entity_type="traffic_report",
            entity_id=report_id,
            actor_user_id=actor_user_id,
            payload_diff={"claim_id": str(claim_id)},
        )

    async def list_for_claim(
        self,
        db: AsyncSession,
        *,
        claim_id: UUID,
        tenant_id: UUID,
        page: int = 1,
        limit: int = 20,
    ) -> tuple[list[TrafficReport], int]:
        offset = (page - 1) * limit
        query = select(TrafficReport).where(
            TrafficReport.claim_id == claim_id, TrafficReport.tenant_id == tenant_id
        )
        count_q = select(func.count()).select_from(query.subquery())
        total = (await db.execute(count_q)).scalar_one()

        query = query.order_by(TrafficReport.created_at.desc()).offset(offset).limit(limit)
        result = await db.execute(query)
        return list(result.scalars().all()), total


traffic_report_service = TrafficReportService()
