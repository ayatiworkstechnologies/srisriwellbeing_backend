"""Ensure an appointment has at most one consultation.

Revision ID: 20260819_0006
Revises: d77f135855d2
Create Date: 2026-08-19
"""

from alembic import op


revision = "20260819_0006"
down_revision = "d77f135855d2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_unique_constraint(
        "uq_consultations_appointment_id",
        "consultations",
        ["appointment_id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_consultations_appointment_id",
        "consultations",
        type_="unique",
    )
