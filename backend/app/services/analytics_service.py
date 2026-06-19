"""Analytics domain service — CU-21 operational KPIs (no AI metrics)."""

from collections import defaultdict
from datetime import date, datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.ai_analysis import AIAnalysis, AIAnalysisKind, AIAnalysisStatus
from app.models.claim import Claim, ClaimStatus
from app.models.claim_request import ClaimRequest, ClaimRequestStatus
from app.models.policy import Policy
from app.models.user import User

# Estados que cuentan como "abiertos" (en gestión, sin decisión final).
_OPEN_STATUSES = {
    ClaimStatus.REGISTERED.value,
    ClaimStatus.IN_REVIEW.value,
    ClaimStatus.OBSERVED.value,
    ClaimStatus.DOCS_PENDING.value,
    ClaimStatus.IN_EVALUATION.value,
}


class AnalyticsService:
    """Aggregated read-only queries for the operational dashboard.

    Todas las queries filtran por ``tenant_id`` (aislamiento multi-tenant).
    No incluye KPIs de IA — esos llegan en Ciclo 8 como fase 2 de CU-21.
    """

    def _claim_filters(
        self,
        query,
        *,
        tenant_id: UUID,
        from_date: date | None,
        to_date: date | None,
        analyst_id: str | None,
    ):
        query = query.where(Claim.tenant_id == tenant_id)
        if from_date:
            query = query.where(Claim.accident_date >= from_date)
        if to_date:
            query = query.where(Claim.accident_date <= to_date)
        if analyst_id:
            query = query.where(Claim.assigned_analyst_id == UUID(analyst_id))
        return query

    async def get_kpis(
        self,
        db: AsyncSession,
        *,
        tenant_id: UUID,
        from_date: date | None = None,
        to_date: date | None = None,
        analyst_id: str | None = None,
    ) -> dict:
        # Conteo de claims por estado.
        claims_q = self._claim_filters(
            select(Claim.status, func.count()).group_by(Claim.status),
            tenant_id=tenant_id,
            from_date=from_date,
            to_date=to_date,
            analyst_id=analyst_id,
        )
        claims_by_status: dict[str, int] = {}
        for status_val, count in (await db.execute(claims_q)).all():
            key = status_val.value if hasattr(status_val, "value") else str(status_val)
            claims_by_status[key] = count
        total_claims = sum(claims_by_status.values())

        # Conteo de solicitudes por estado (sin filtro de analista; las requests no
        # tienen analista asignado de la misma forma).
        req_q = select(ClaimRequest.status, func.count()).where(
            ClaimRequest.tenant_id == tenant_id
        ).group_by(ClaimRequest.status)
        requests_by_status: dict[str, int] = {}
        for status_val, count in (await db.execute(req_q)).all():
            key = status_val.value if hasattr(status_val, "value") else str(status_val)
            requests_by_status[key] = count
        total_requests = sum(requests_by_status.values())

        rejected_at_intake = requests_by_status.get(
            ClaimRequestStatus.REJECTED_AT_INTAKE.value, 0
        )
        intake_rejection_rate = (
            rejected_at_intake / total_requests if total_requests else 0.0
        )

        approved = claims_by_status.get(ClaimStatus.APPROVED.value, 0)
        rejected = claims_by_status.get(ClaimStatus.REJECTED.value, 0)
        decided_total = approved + rejected
        approval_rate = approved / decided_total if decided_total else 0.0

        open_claims = sum(
            count for status, count in claims_by_status.items() if status in _OPEN_STATUSES
        )

        # Promedio de días registrado → decidido.
        decided_q = self._claim_filters(
            select(Claim.created_at, Claim.decided_at).where(
                Claim.decided_at.is_not(None)
            ),
            tenant_id=tenant_id,
            from_date=from_date,
            to_date=to_date,
            analyst_id=analyst_id,
        )
        deltas: list[float] = []
        for created_at, decided_at in (await db.execute(decided_q)).all():
            if created_at and decided_at:
                deltas.append((decided_at - created_at).total_seconds() / 86400.0)
        avg_days_to_decision = round(sum(deltas) / len(deltas), 2) if deltas else None

        return {
            "total_claims": total_claims,
            "total_requests": total_requests,
            "claims_by_status": claims_by_status,
            "requests_by_status": requests_by_status,
            "intake_rejection_rate": round(intake_rejection_rate, 4),
            "approval_rate": round(approval_rate, 4),
            "avg_days_to_decision": avg_days_to_decision,
            "open_claims": open_claims,
        }

    async def status_distribution(
        self,
        db: AsyncSession,
        *,
        tenant_id: UUID,
        from_date: date | None = None,
        to_date: date | None = None,
        analyst_id: str | None = None,
    ) -> tuple[list[dict], int]:
        query = self._claim_filters(
            select(Claim.status, func.count()).group_by(Claim.status),
            tenant_id=tenant_id,
            from_date=from_date,
            to_date=to_date,
            analyst_id=analyst_id,
        )
        items: list[dict] = []
        total = 0
        for status_val, count in (await db.execute(query)).all():
            key = status_val.value if hasattr(status_val, "value") else str(status_val)
            items.append({"status": key, "count": count})
            total += count
        return items, total

    async def timeline(
        self,
        db: AsyncSession,
        *,
        tenant_id: UUID,
        from_date: date | None = None,
        to_date: date | None = None,
        analyst_id: str | None = None,
    ) -> list[dict]:
        # Agregamos por día en Python para portabilidad SQLite/PostgreSQL.
        query = self._claim_filters(
            select(Claim.created_at),
            tenant_id=tenant_id,
            from_date=from_date,
            to_date=to_date,
            analyst_id=analyst_id,
        )
        buckets: dict[str, int] = defaultdict(int)
        for (created_at,) in (await db.execute(query)).all():
            if created_at is None:
                continue
            day = created_at.date() if isinstance(created_at, datetime) else created_at
            buckets[day.isoformat()] += 1
        return [
            {"date": day, "count": buckets[day]} for day in sorted(buckets.keys())
        ]

    async def coverage_distribution(
        self,
        db: AsyncSession,
        *,
        tenant_id: UUID,
    ) -> tuple[list[dict], int]:
        # Distribución de claims por tipo de cobertura de su póliza.
        query = (
            select(Policy.coverage_type, func.count())
            .select_from(Claim)
            .join(Policy, Policy.id == Claim.policy_id)
            .where(Claim.tenant_id == tenant_id)
            .group_by(Policy.coverage_type)
        )
        items: list[dict] = []
        total = 0
        for coverage_type, count in (await db.execute(query)).all():
            items.append({"coverage_type": coverage_type or "sin_cobertura", "count": count})
            total += count
        return items, total

    async def analyst_productivity(
        self,
        db: AsyncSession,
        *,
        tenant_id: UUID,
        from_date: date | None = None,
        to_date: date | None = None,
    ) -> list[dict]:
        # Asignados por analista.
        assigned_q = self._claim_filters(
            select(Claim.assigned_analyst_id, func.count())
            .where(Claim.assigned_analyst_id.is_not(None))
            .group_by(Claim.assigned_analyst_id),
            tenant_id=tenant_id,
            from_date=from_date,
            to_date=to_date,
            analyst_id=None,
        )
        assigned_map: dict[UUID, int] = {}
        for analyst_id, count in (await db.execute(assigned_q)).all():
            assigned_map[analyst_id] = count

        # Decididos por analista (claims con decisión, atribuidos al analista asignado).
        decided_q = self._claim_filters(
            select(Claim.assigned_analyst_id, func.count())
            .where(
                Claim.assigned_analyst_id.is_not(None),
                Claim.decided_at.is_not(None),
            )
            .group_by(Claim.assigned_analyst_id),
            tenant_id=tenant_id,
            from_date=from_date,
            to_date=to_date,
            analyst_id=None,
        )
        decided_map: dict[UUID, int] = {}
        for analyst_id, count in (await db.execute(decided_q)).all():
            decided_map[analyst_id] = count

        analyst_ids = set(assigned_map) | set(decided_map)
        if not analyst_ids:
            return []

        names_q = select(User.id, User.full_name).where(
            User.id.in_(analyst_ids), User.tenant_id == tenant_id
        )
        names = {uid: name for uid, name in (await db.execute(names_q)).all()}

        items: list[dict] = []
        for aid in analyst_ids:
            items.append(
                {
                    "analyst_id": str(aid),
                    "analyst_name": names.get(aid, "—"),
                    "assigned": assigned_map.get(aid, 0),
                    "decided": decided_map.get(aid, 0),
                }
            )
        items.sort(key=lambda x: x["assigned"], reverse=True)
        return items

    async def ai_kpis(
        self,
        db: AsyncSession,
        *,
        tenant_id: UUID,
    ) -> dict:
        """Fase 2 de CU-21 (Ciclo 8): KPIs de IA para el dashboard.

        - suspicious_claims: claims con fraud_score > umbral de alerta.
        - high_fraud_rate: proporción de claims (con score) sobre el umbral.
        - top_inconsistencies: campos más reportados por el LLM, agregados
          sobre el análisis de inconsistencias más reciente por claim.
        """
        # Claims sospechosos (fraud_score por encima del umbral de alerta).
        threshold = settings.AI_FRAUD_ALERT_THRESHOLD
        scored_q = select(Claim.fraud_score).where(
            Claim.tenant_id == tenant_id, Claim.fraud_score.is_not(None)
        )
        scores = [float(s) for (s,) in (await db.execute(scored_q)).all() if s is not None]
        suspicious = sum(1 for s in scores if s > threshold)
        high_fraud_rate = round(suspicious / len(scores), 4) if scores else 0.0

        # Inconsistencias: tomamos el análisis más reciente por claim (done) y
        # contamos los campos afectados. Agregación en Python (portable).
        inc_q = (
            select(AIAnalysis.claim_id, AIAnalysis.payload, AIAnalysis.created_at)
            .where(
                AIAnalysis.tenant_id == tenant_id,
                AIAnalysis.kind == AIAnalysisKind.INCONSISTENCY,
                AIAnalysis.status == AIAnalysisStatus.DONE,
            )
            .order_by(AIAnalysis.created_at.desc())
        )
        seen_claims: set = set()
        field_counts: dict[str, int] = defaultdict(int)
        total_findings = 0
        for claim_id, payload, _created in (await db.execute(inc_q)).all():
            if claim_id in seen_claims:
                continue  # solo el más reciente por claim
            seen_claims.add(claim_id)
            for finding in (payload or {}).get("findings", []):
                field = (finding or {}).get("field") or "(sin campo)"
                field_counts[field] += 1
                total_findings += 1

        top_inconsistencies = sorted(
            ({"field": f, "count": c} for f, c in field_counts.items()),
            key=lambda x: x["count"],
            reverse=True,
        )[:5]

        return {
            "suspicious_claims": suspicious,
            "scored_claims": len(scores),
            "high_fraud_rate": high_fraud_rate,
            "fraud_alert_threshold": threshold,
            "total_inconsistency_findings": total_findings,
            "top_inconsistencies": top_inconsistencies,
        }


analytics_service = AnalyticsService()
