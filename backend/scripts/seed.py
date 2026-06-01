"""Seed de datos de prueba para desarrollo."""

import asyncio
from datetime import date, datetime, time, timezone
from uuid import uuid4

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import select

from app.core.config import settings
from app.core.security import hash_password
from app.models.tenant import Tenant
from app.models.user import User, Role
from app.models.policyholder import Policyholder
from app.models.policy import Policy
from app.models.vehicle import Vehicle
from app.models.claim_request import ClaimRequest, ClaimRequestStatus
from app.models.claim import Claim, ClaimStatus, ClaimSource
from app.models.state_transition import StateTransition, SubjectType


TENANT = {"name": "Aseguradora Demo", "slug": "demo"}

USERS = [
    {"email": "admin@demo.com",      "password": "Admin123!", "full_name": "Admin Demo",      "role": Role.ADMIN},
    {"email": "supervisor@demo.com", "password": "Admin123!", "full_name": "Supervisor Demo", "role": Role.SUPERVISOR},
    {"email": "analista@demo.com",   "password": "Admin123!", "full_name": "Analista Demo",   "role": Role.ANALYST},
    {"email": "analista2@demo.com",  "password": "Admin123!", "full_name": "Analista Dos",    "role": Role.ANALYST},
]

POLICYHOLDERS = [
    {"document_id": "12345678-LP", "full_name": "Juan Pérez",      "phone": "77712345", "email": "juan@mail.com", "address": "Av. Siempre Viva 742"},
    {"document_id": "87654321-CB", "full_name": "María Gómez",     "phone": "77754321", "email": "maria@mail.com", "address": "Calle Falsa 123"},
    {"document_id": "45678912-SC", "full_name": "Carlos Choque",   "phone": "77798765", "email": "carlos@mail.com", "address": "Zona Central 456"},
    {"document_id": "32165498-OR", "full_name": "Ana Quispe",      "phone": "77734567", "email": "ana@mail.com", "address": "Av. América 100"},
]


async def seed() -> None:
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async with session_factory() as db:
        # ── Tenant ───────────────────────────────────────────────
        existing = await db.execute(select(Tenant).where(Tenant.slug == TENANT["slug"]))
        tenant = existing.scalar_one_or_none()
        if not tenant:
            tenant = Tenant(**TENANT)
            db.add(tenant)
            await db.flush()
            print(f"✅ Tenant creado: {tenant.name} (slug={tenant.slug})")
        else:
            print(f"⚠️  Tenant ya existe: {tenant.slug}")

        tid = tenant.id

        # ── Users ────────────────────────────────────────────────
        user_ids: dict[str, str] = {}
        for u in USERS:
            existing_user = await db.execute(
                select(User).where(User.email == u["email"], User.tenant_id == tid)
            )
            if existing_user.scalar_one_or_none():
                print(f"⚠️  Usuario ya existe: {u['email']}")
                continue
            user = User(
                email=u["email"],
                hashed_password=hash_password(u["password"]),
                full_name=u["full_name"],
                role=u["role"],
                tenant_id=tid,
            )
            db.add(user)
            await db.flush()
            user_ids[u["email"]] = user.id
            print(f"✅ Usuario creado: {u['email']} ({u['role'].value}) — pass: {u['password']}")

        analyst_id = user_ids.get("analista@demo.com")
        analyst2_id = user_ids.get("analista2@demo.com")

        # ── Policyholders ────────────────────────────────────────
        ph_ids: list[str] = []
        for ph_data in POLICYHOLDERS:
            ph_row = (await db.execute(
                select(Policyholder).where(
                    Policyholder.document_id == ph_data["document_id"],
                    Policyholder.tenant_id == tid,
                )
            )).scalar_one_or_none()
            if ph_row:
                print(f"⚠️  Asegurado ya existe: {ph_data['document_id']}")
                ph_ids.append(ph_row.id)
                continue
            ph = Policyholder(tenant_id=tid, **ph_data)
            db.add(ph)
            await db.flush()
            ph_ids.append(ph.id)
            print(f"✅ Asegurado creado: {ph.full_name} ({ph.document_id})")
        await db.flush()

        # ── Policies ─────────────────────────────────────────────
        p1 = (await db.execute(
            select(Policy).where(Policy.tenant_id == tid, Policy.policy_number == "POL-2026-001")
        )).scalar_one_or_none()
        if not p1:
            p1 = Policy(
                tenant_id=tid,
                policy_number="POL-2026-001",
                policyholder_id=ph_ids[0],
                valid_from=date(2026, 1, 1),
                valid_to=date(2026, 12, 31),
                coverage_type="Todo Riesgo",
                exclusions="Daños por terremoto",
            )
            db.add(p1)
            await db.flush()
            print("✅ Póliza creada: POL-2026-001 (Todo Riesgo)")

        p2 = (await db.execute(
            select(Policy).where(Policy.tenant_id == tid, Policy.policy_number == "POL-2026-002")
        )).scalar_one_or_none()
        if not p2:
            p2 = Policy(
                tenant_id=tid,
                policy_number="POL-2026-002",
                policyholder_id=ph_ids[1],
                valid_from=date(2025, 6, 1),
                valid_to=date(2026, 6, 1),
                coverage_type="Terceros Completo",
                status="active",
            )
            db.add(p2)
            await db.flush()
            print("✅ Póliza creada: POL-2026-002 (Terceros Completo)")

        p3 = (await db.execute(
            select(Policy).where(Policy.tenant_id == tid, Policy.policy_number == "POL-2026-003")
        )).scalar_one_or_none()
        if not p3:
            p3 = Policy(
                tenant_id=tid,
                policy_number="POL-2026-003",
                policyholder_id=ph_ids[2],
                valid_from=date(2026, 3, 1),
                valid_to=date(2027, 3, 1),
                coverage_type="Todo Riesgo",
                status="active",
            )
            db.add(p3)
            await db.flush()
            print("✅ Póliza creada: POL-2026-003 (Todo Riesgo)")

        # ── Vehicles ─────────────────────────────────────────────
        v1 = (await db.execute(
            select(Vehicle).where(Vehicle.tenant_id == tid, Vehicle.plate == "ABC-123")
        )).scalar_one_or_none()
        if not v1:
            v1 = Vehicle(
                tenant_id=tid,
                plate="ABC-123",
                make="Toyota",
                model="Corolla",
                year=2022,
                color="Blanco",
                vehicle_type="sedan",
                policy_id=p1.id,
            )
            db.add(v1)
            await db.flush()
            print("✅ Vehículo creado: ABC-123 (Toyota Corolla)")

        v2 = (await db.execute(
            select(Vehicle).where(Vehicle.tenant_id == tid, Vehicle.plate == "XYZ-789")
        )).scalar_one_or_none()
        if not v2:
            v2 = Vehicle(
                tenant_id=tid,
                plate="XYZ-789",
                make="Nissan",
                model="Sentra",
                year=2024,
                color="Rojo",
                vehicle_type="sedan",
                policy_id=p2.id,
            )
            db.add(v2)
            await db.flush()
            print("✅ Vehículo creado: XYZ-789 (Nissan Sentra)")

        v3 = (await db.execute(
            select(Vehicle).where(Vehicle.tenant_id == tid, Vehicle.plate == "LMN-456")
        )).scalar_one_or_none()
        if not v3:
            v3 = Vehicle(
                tenant_id=tid,
                plate="LMN-456",
                make="Suzuki",
                model="Grand Vitara",
                year=2023,
                color="Negro",
                vehicle_type="suv",
                policy_id=p3.id,
            )
            db.add(v3)
            await db.flush()
            print("✅ Vehículo creado: LMN-456 (Suzuki Grand Vitara)")

        await db.flush()

        # ── Claim Requests ───────────────────────────────────────
        now = datetime.utcnow()

        # Only seed if no requests exist yet
        existing_req = await db.execute(
            select(ClaimRequest).where(ClaimRequest.tenant_id == tid).limit(1)
        )
        if existing_req.scalar_one_or_none():
            print("⚠️  Ya existen claim_requests, saltando seed de solicitudes")
        else:
            reqs = [
                # submitted — ready for intake
                ClaimRequest(
                    tenant_id=tid,
                    request_number="REQ-2026-000001",
                    status=ClaimRequestStatus.SUBMITTED,
                    policyholder_id=ph_ids[0],
                    policy_id=p1.id,
                    vehicle_id=v1.id,
                    accident_date=date(2026, 5, 15),
                    accident_time=time(14, 30),
                    accident_location="Av. Blanco Galindo km 5, Cochabamba",
                    accident_description="Colisión por alcance en semáforo. El vehículo de atrás no frenó a tiempo.",
                    reported_damages="Parachoques trasero dañado, faro derecho roto, maletera deformada.",
                    submitted_at=now,
                    created_at=now,
                ),
                ClaimRequest(
                    tenant_id=tid,
                    request_number="REQ-2026-000002",
                    status=ClaimRequestStatus.SUBMITTED,
                    policyholder_id=ph_ids[1],
                    policy_id=p2.id,
                    vehicle_id=v2.id,
                    accident_date=date(2026, 5, 20),
                    accident_time=time(9, 15),
                    accident_location="Calle Sucre 150, La Paz",
                    accident_description="Choque lateral en intersección. Otro vehículo no respetó el alto.",
                    reported_damages="Puerta del conductor raspada y abollada, espejo lateral roto.",
                    submitted_at=now,
                    created_at=now,
                ),
                # draft — incomplete request from mobile app (simulated)
                ClaimRequest(
                    tenant_id=tid,
                    status=ClaimRequestStatus.DRAFT,
                    policyholder_id=ph_ids[2],
                    policy_id=p3.id,
                    vehicle_id=v3.id,
                    accident_date=date(2026, 5, 25),
                    accident_location="Av. Circunvalación, Santa Cruz",
                    accident_description="Derrape por lluvia y colisión contra baranda de contención.",
                    created_at=now,
                ),
                # under_intake_review — taken by analyst
                ClaimRequest(
                    tenant_id=tid,
                    request_number="REQ-2026-000003",
                    status=ClaimRequestStatus.UNDER_INTAKE_REVIEW,
                    policyholder_id=ph_ids[0],
                    policy_id=p1.id,
                    vehicle_id=v1.id,
                    accident_date=date(2026, 5, 10),
                    accident_time=time(18, 45),
                    accident_location="Av. Petrolera, Cochabamba",
                    accident_description="Impacto contra objeto fijo (poste de luz) al esquivar a un peatón.",
                    reported_damages="Parachoques delantero, radiador y faro izquierdo dañados.",
                    submitted_at=now,
                    reviewed_by_user_id=analyst_id,
                    created_at=now,
                ),
                # rejected_at_intake
                ClaimRequest(
                    tenant_id=tid,
                    request_number="REQ-2026-000004",
                    status=ClaimRequestStatus.REJECTED_AT_INTAKE,
                    policyholder_id=ph_ids[3],
                    policy_id=p2.id,
                    vehicle_id=v2.id,
                    accident_date=date(2026, 1, 15),
                    accident_location="Desconocida",
                    accident_description="Supuesto robo del vehículo.",
                    submitted_at=datetime(2026, 4, 1, ),
                    reviewed_by_user_id=analyst2_id,
                    intake_decision_reason="La póliza no estaba vigente en la fecha del supuesto accidente. El vehículo reportado no coincide con el registrado en póliza.",
                    created_at=datetime(2026, 4, 1, ),
                ),
            ]
            for r in reqs:
                db.add(r)
                await db.flush()
                if r.status == ClaimRequestStatus.SUBMITTED:
                    t = StateTransition(
                        tenant_id=tid,
                        subject_type=SubjectType.CLAIM_REQUEST,
                        subject_id=r.id,
                        from_status=ClaimRequestStatus.DRAFT.value,
                        to_status=ClaimRequestStatus.SUBMITTED.value,
                        actor_user_id=analyst_id,
                    )
                    db.add(t)
                elif r.status == ClaimRequestStatus.UNDER_INTAKE_REVIEW:
                    t = StateTransition(
                        tenant_id=tid,
                        subject_type=SubjectType.CLAIM_REQUEST,
                        subject_id=r.id,
                        from_status=ClaimRequestStatus.SUBMITTED.value,
                        to_status=ClaimRequestStatus.UNDER_INTAKE_REVIEW.value,
                        actor_user_id=analyst_id,
                    )
                    db.add(t)
                elif r.status == ClaimRequestStatus.REJECTED_AT_INTAKE:
                    t = StateTransition(
                        tenant_id=tid,
                        subject_type=SubjectType.CLAIM_REQUEST,
                        subject_id=r.id,
                        from_status=ClaimRequestStatus.SUBMITTED.value,
                        to_status=ClaimRequestStatus.REJECTED_AT_INTAKE.value,
                        reason=r.intake_decision_reason,
                        actor_user_id=analyst2_id,
                    )
                    db.add(t)
            print("✅ 5 solicitudes (claim_requests) creadas")

        # ── Claims (expedientes) ─────────────────────────────────
        existing_claims = await db.execute(
            select(Claim).where(Claim.tenant_id == tid).limit(1)
        )
        if existing_claims.scalar_one_or_none():
            print("⚠️  Ya existen claims, saltando seed de expedientes")
        else:
            claims_data = [
                Claim(
                    tenant_id=tid,
                    claim_number="EXP-2026-000001",
                    policyholder_id=ph_ids[0],
                    policy_id=p1.id,
                    vehicle_id=v1.id,
                    status=ClaimStatus.IN_REVIEW,
                    source=ClaimSource.MOBILE_APP,
                    accident_date=date(2026, 4, 20),
                    accident_time=time(8, 30),
                    accident_location="Av. Oquendo, Cochabamba",
                    accident_description="Colisión frontal con otro vehículo en intersección sin semáforo.",
                    reported_damages="Capó, radiador, y faros delanteros gravemente dañados.",
                    created_by_user_id=analyst_id,
                    assigned_analyst_id=analyst_id,
                    created_at=datetime(2026, 4, 25, ),
                ),
                Claim(
                    tenant_id=tid,
                    claim_number="EXP-2026-000002",
                    policyholder_id=ph_ids[1],
                    policy_id=p2.id,
                    vehicle_id=v2.id,
                    status=ClaimStatus.OBSERVED,
                    source=ClaimSource.INTERNAL,
                    accident_date=date(2026, 5, 5),
                    accident_time=time(17, 0),
                    accident_location="Av. Montes, La Paz",
                    accident_description="Vehículo estacionado fue impactado por otro que se dio a la fuga.",
                    reported_damages="Lateral derecho abollado, puerta trasera no cierra.",
                    created_by_user_id=analyst2_id,
                    assigned_analyst_id=analyst2_id,
                    created_at=datetime(2026, 5, 10, ),
                ),
                Claim(
                    tenant_id=tid,
                    claim_number="EXP-2026-000003",
                    policyholder_id=ph_ids[2],
                    policy_id=p3.id,
                    vehicle_id=v3.id,
                    status=ClaimStatus.IN_EVALUATION,
                    source=ClaimSource.MOBILE_APP,
                    accident_date=date(2026, 5, 12),
                    accident_time=time(11, 20),
                    accident_location="Av. Cristo Redentor, Santa Cruz",
                    accident_description="Atropello a animal suelto en carretera. Daños en parte frontal.",
                    reported_damages="Parachoques delantero roto, radiador perforado.",
                    created_by_user_id=analyst_id,
                    assigned_analyst_id=analyst_id,
                    created_at=datetime(2026, 5, 14, ),
                ),
                Claim(
                    tenant_id=tid,
                    claim_number="EXP-2026-000004",
                    policyholder_id=ph_ids[0],
                    policy_id=p1.id,
                    vehicle_id=v1.id,
                    status=ClaimStatus.APPROVED,
                    source=ClaimSource.INTERNAL,
                    accident_date=date(2026, 3, 1),
                    accident_time=time(13, 0),
                    accident_location="Av. América, Oruro",
                    accident_description="Granizo causó daños en carrocería y parabrisas.",
                    reported_damages="Parabrisas roto, capó con abolladuras múltiples por granizo.",
                    created_by_user_id=analyst_id,
                    assigned_analyst_id=analyst_id,
                    created_at=datetime(2026, 3, 5, ),
                ),
                Claim(
                    tenant_id=tid,
                    claim_number="EXP-2026-000005",
                    policyholder_id=ph_ids[3],
                    policy_id=p2.id,
                    vehicle_id=v2.id,
                    status=ClaimStatus.REGISTERED,
                    source=ClaimSource.INTERNAL,
                    accident_date=date(2026, 5, 28),
                    accident_location="Zona Sur, La Paz",
                    accident_description="Recién registrado. Pendiente de revisión.",
                    created_by_user_id=analyst2_id,
                    assigned_analyst_id=analyst2_id,
                    created_at=datetime(2026, 5, 29, ),
                ),
            ]

            for c in claims_data:
                db.add(c)
                await db.flush()
                t = StateTransition(
                    tenant_id=tid,
                    subject_type=SubjectType.CLAIM,
                    subject_id=c.id,
                    from_status=None,
                    to_status=c.status.value,
                    actor_user_id=c.created_by_user_id,
                )
                db.add(t)
            print("✅ 5 expedientes (claims) creados")

        await db.commit()

    await engine.dispose()
    print("\n🎉 Seed completado.")


if __name__ == "__main__":
    asyncio.run(seed())
