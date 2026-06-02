"""normalize_enum_labels_to_lowercase

Revision ID: b2f9c1d8e3a4
Revises: 86aa3d1ad317
Create Date: 2026-06-02 16:00:00.000000

Renames postgres enum labels from UPPERCASE (Python enum NAMES) to lowercase
(Python enum VALUES) so every model can consistently use
`SQLEnum(..., values_callable=lambda x: [e.value for e in x])`.

Each rename is wrapped in a DO block that checks pg_enum first, so the
migration is idempotent — safe on databases where some enums were already
renamed manually (e.g. Cycle 3 local DBs) and safe on fresh clones.
"""

from typing import Sequence, Union

from alembic import op


revision: str = 'b2f9c1d8e3a4'
down_revision: Union[str, None] = '86aa3d1ad317'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


ENUM_RENAMES: dict[str, list[tuple[str, str]]] = {
    'claimstatus': [
        ('REGISTERED', 'registered'),
        ('IN_REVIEW', 'in_review'),
        ('OBSERVED', 'observed'),
        ('DOCS_PENDING', 'docs_pending'),
        ('IN_EVALUATION', 'in_evaluation'),
        ('APPROVED', 'approved'),
        ('REJECTED', 'rejected'),
        ('CLOSED', 'closed'),
    ],
    'claimsource': [
        ('MOBILE_APP', 'mobile_app'),
        ('INTERNAL', 'internal'),
    ],
    'claimdecision': [
        ('APPROVED', 'approved'),
        ('REJECTED', 'rejected'),
    ],
    'claimrequeststatus': [
        ('DRAFT', 'draft'),
        ('SUBMITTED', 'submitted'),
        ('UNDER_INTAKE_REVIEW', 'under_intake_review'),
        ('FORMALIZED', 'formalized'),
        ('REJECTED_AT_INTAKE', 'rejected_at_intake'),
    ],
    'thirdpartykind': [
        ('DRIVER', 'driver'),
        ('WITNESS', 'witness'),
        ('VICTIM', 'victim'),
        ('VEHICLE_OWNER', 'vehicle_owner'),
    ],
    'documentrequeststatus': [
        ('PENDING', 'pending'),
        ('SUBMITTED', 'submitted'),
        ('WAIVED', 'waived'),
    ],
    'evidencetype': [
        ('PHOTO', 'photo'),
        ('VIDEO', 'video'),
        ('INVOICE', 'invoice'),
        ('TECHNICAL_REPORT', 'technical_report'),
        ('SKETCH', 'sketch'),
        ('POLICE_REPORT', 'police_report'),
        ('PERSONAL_DOC', 'personal_doc'),
        ('OTHER', 'other'),
    ],
}


def _rename_if_exists(enum_name: str, old: str, new: str) -> None:
    """Emit a DO block that renames only if the old label still exists."""
    op.execute(
        f"""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM pg_enum
                JOIN pg_type ON pg_type.oid = enumtypid
                WHERE typname = '{enum_name}' AND enumlabel = '{old}'
            ) THEN
                ALTER TYPE {enum_name} RENAME VALUE '{old}' TO '{new}';
            END IF;
        END
        $$;
        """
    )


def upgrade() -> None:
    for enum_name, renames in ENUM_RENAMES.items():
        for old, new in renames:
            _rename_if_exists(enum_name, old, new)


def downgrade() -> None:
    for enum_name, renames in ENUM_RENAMES.items():
        for old, new in renames:
            _rename_if_exists(enum_name, new, old)
