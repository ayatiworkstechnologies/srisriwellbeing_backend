"""Initial Week 1-4 application schema.

Revision ID: 20260804_0001
Revises:
Create Date: 2026-08-04
"""

import app.models.model_registry  # noqa: F401
import sqlalchemy as sa
from alembic import op
from app.models.base import Base

revision = "20260804_0001"
down_revision = None
branch_labels = None
depends_on = None


# Keep this historical migration frozen to the tables that belonged to the
# Week 1-4 schema when the revision was created.  Using every table currently
# registered on Base would make a fresh install create tables owned by later
# migrations, causing those migrations to fail with duplicate-table errors.
INITIAL_TABLE_NAMES = {
    "audit_logs",
    "consent_templates",
    "login_attempts",
    "password_reset_tokens",
    "patient_addresses",
    "patient_allergies",
    "patient_conditions",
    "patient_consents",
    "patient_documents",
    "patient_duplicate_matches",
    "patient_emergency_contacts",
    "patient_existing_medicines",
    "patient_identifiers",
    "patient_medical_histories",
    "patient_surgeries",
    "patients",
    "permissions",
    "refresh_tokens",
    "role_permissions",
    "roles",
    "user_roles",
    "user_sessions",
    "users",
}


def _initial_tables():
    return [
        table
        for table in Base.metadata.sorted_tables
        if table.name in INITIAL_TABLE_NAMES
        and table.name != "permissions"
    ]


def upgrade() -> None:
    # ``permissions.name`` belongs to the next migration and must not leak
    # into this revision through the current ORM model.
    op.create_table(
        "permissions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("module", sa.String(length=100), nullable=False),
        sa.Column("action", sa.String(length=100), nullable=False),
        sa.Column("code", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "is_active",
            sa.Boolean(),
            server_default="1",
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_permissions_code"),
        "permissions",
        ["code"],
        unique=True,
    )
    op.create_index(
        op.f("ix_permissions_module"),
        "permissions",
        ["module"],
        unique=False,
    )

    Base.metadata.create_all(
        bind=op.get_bind(),
        tables=_initial_tables(),
        checkfirst=True,
    )


def downgrade() -> None:
    Base.metadata.drop_all(
        bind=op.get_bind(),
        tables=list(reversed(_initial_tables())),
        checkfirst=True,
    )
    op.drop_index(op.f("ix_permissions_module"), table_name="permissions")
    op.drop_index(op.f("ix_permissions_code"), table_name="permissions")
    op.drop_table("permissions")
