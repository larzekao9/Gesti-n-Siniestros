"""create insured channel tables (Ciclo 7)

Crea las tablas del canal asegurado y enlaza las tablas existentes:
- policyholder_accounts (login del asegurado en la app móvil)
- account_refresh_tokens (refresh rotativo del canal asegurado)
- device_tokens (Expo push tokens)
- ALTER claim_requests + created_by_account_id
- ALTER evidences + uploaded_by_account_id
- ALTER notifications: FK recipient_account_id -> policyholder_accounts

Revision ID: d7a3c9e1f5b2
Revises: e0fb442c7e1e
Create Date: 2026-06-03

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "d7a3c9e1f5b2"
down_revision: Union[str, None] = "e0fb442c7e1e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── policyholder_accounts ─────────────────────────────────────────
    op.create_table(
        "policyholder_accounts",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("policyholder_id", sa.Uuid(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("activation_token", sa.String(length=64), nullable=True),
        sa.Column("activation_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("password_reset_token", sa.String(length=64), nullable=True),
        sa.Column("password_reset_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("mfa_secret", sa.String(length=32), nullable=True),
        sa.Column("mfa_enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["policyholder_id"], ["policyholders.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_policyholder_accounts_tenant_id"),
        "policyholder_accounts",
        ["tenant_id"],
        unique=False,
    )
    op.create_index(
        "ix_policyholder_accounts_tenant_email",
        "policyholder_accounts",
        ["tenant_id", "email"],
        unique=True,
    )
    op.create_index(
        "ix_policyholder_accounts_activation_token",
        "policyholder_accounts",
        ["activation_token"],
        unique=True,
    )
    op.create_index(
        "ix_policyholder_accounts_reset_token",
        "policyholder_accounts",
        ["password_reset_token"],
        unique=True,
    )

    # ── account_refresh_tokens ────────────────────────────────────────
    op.create_table(
        "account_refresh_tokens",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("token", sa.String(length=500), nullable=False),
        sa.Column("account_id", sa.Uuid(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["account_id"], ["policyholder_accounts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_account_refresh_tokens_tenant_id"),
        "account_refresh_tokens",
        ["tenant_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_account_refresh_tokens_token"),
        "account_refresh_tokens",
        ["token"],
        unique=True,
    )

    # ── device_tokens ─────────────────────────────────────────────────
    op.create_table(
        "device_tokens",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("account_id", sa.Uuid(), nullable=False),
        sa.Column("expo_push_token", sa.String(length=255), nullable=False),
        sa.Column(
            "platform",
            sa.Enum("ios", "android", name="deviceplatform"),
            nullable=False,
        ),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["account_id"], ["policyholder_accounts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_device_tokens_tenant_id"),
        "device_tokens",
        ["tenant_id"],
        unique=False,
    )
    op.create_index(
        "ix_device_tokens_expo_token",
        "device_tokens",
        ["expo_push_token"],
        unique=True,
    )
    op.create_index(
        "ix_device_tokens_tenant_account",
        "device_tokens",
        ["tenant_id", "account_id"],
        unique=False,
    )

    # ── ALTER claim_requests: created_by_account_id ───────────────────
    op.add_column(
        "claim_requests",
        sa.Column("created_by_account_id", sa.Uuid(), nullable=True),
    )
    op.create_foreign_key(
        "fk_claim_requests_created_by_account",
        "claim_requests",
        "policyholder_accounts",
        ["created_by_account_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # ── ALTER evidences: uploaded_by_account_id ───────────────────────
    op.add_column(
        "evidences",
        sa.Column("uploaded_by_account_id", sa.Uuid(), nullable=True),
    )
    op.create_foreign_key(
        "fk_evidences_uploaded_by_account",
        "evidences",
        "policyholder_accounts",
        ["uploaded_by_account_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # ── ALTER notifications: FK recipient_account_id ──────────────────
    op.create_foreign_key(
        "fk_notifications_recipient_account",
        "notifications",
        "policyholder_accounts",
        ["recipient_account_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # ── ALTER audit_logs: actor_account_id ────────────────────────────
    op.add_column(
        "audit_logs",
        sa.Column("actor_account_id", sa.Uuid(), nullable=True),
    )
    op.create_foreign_key(
        "fk_audit_logs_actor_account",
        "audit_logs",
        "policyholder_accounts",
        ["actor_account_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # ── ALTER state_transitions: actor_account_id ─────────────────────
    op.add_column(
        "state_transitions",
        sa.Column("actor_account_id", sa.Uuid(), nullable=True),
    )
    op.create_foreign_key(
        "fk_state_transitions_actor_account",
        "state_transitions",
        "policyholder_accounts",
        ["actor_account_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_state_transitions_actor_account", "state_transitions", type_="foreignkey"
    )
    op.drop_column("state_transitions", "actor_account_id")
    op.drop_constraint("fk_audit_logs_actor_account", "audit_logs", type_="foreignkey")
    op.drop_column("audit_logs", "actor_account_id")
    op.drop_constraint(
        "fk_notifications_recipient_account", "notifications", type_="foreignkey"
    )
    op.drop_constraint(
        "fk_evidences_uploaded_by_account", "evidences", type_="foreignkey"
    )
    op.drop_column("evidences", "uploaded_by_account_id")
    op.drop_constraint(
        "fk_claim_requests_created_by_account", "claim_requests", type_="foreignkey"
    )
    op.drop_column("claim_requests", "created_by_account_id")

    op.drop_index("ix_device_tokens_tenant_account", table_name="device_tokens")
    op.drop_index("ix_device_tokens_expo_token", table_name="device_tokens")
    op.drop_index(op.f("ix_device_tokens_tenant_id"), table_name="device_tokens")
    op.drop_table("device_tokens")

    op.drop_index(
        op.f("ix_account_refresh_tokens_token"), table_name="account_refresh_tokens"
    )
    op.drop_index(
        op.f("ix_account_refresh_tokens_tenant_id"), table_name="account_refresh_tokens"
    )
    op.drop_table("account_refresh_tokens")

    op.drop_index(
        "ix_policyholder_accounts_reset_token", table_name="policyholder_accounts"
    )
    op.drop_index(
        "ix_policyholder_accounts_activation_token", table_name="policyholder_accounts"
    )
    op.drop_index(
        "ix_policyholder_accounts_tenant_email", table_name="policyholder_accounts"
    )
    op.drop_index(
        op.f("ix_policyholder_accounts_tenant_id"), table_name="policyholder_accounts"
    )
    op.drop_table("policyholder_accounts")

    op.execute("DROP TYPE IF EXISTS deviceplatform")
