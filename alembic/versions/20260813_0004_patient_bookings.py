"""Create patient booking and reschedule history tables.

Revision ID: 20260813_0004
Revises: a1b358e7fc55
Create Date: 2026-08-13
"""

from alembic import op
import sqlalchemy as sa


revision = "20260813_0004"
down_revision = "a1b358e7fc55"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "patient_bookings",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("patient_id", sa.Integer(), nullable=False),
        sa.Column("booking_date", sa.Date(), nullable=False),
        sa.Column("start_time", sa.Time(), nullable=False),
        sa.Column("end_time", sa.Time(), nullable=False),
        sa.Column(
            "status",
            sa.String(length=30),
            nullable=False,
            server_default="BOOKED",
        ),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column(
            "reschedule_count",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(
            ["patient_id"],
            ["patients.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_patient_bookings_patient_id",
        "patient_bookings",
        ["patient_id"],
    )
    op.create_index(
        "ix_patient_bookings_booking_date",
        "patient_bookings",
        ["booking_date"],
    )
    op.create_index(
        "ix_patient_bookings_status",
        "patient_bookings",
        ["status"],
    )
    op.create_index(
        "ix_patient_bookings_date_time",
        "patient_bookings",
        ["booking_date", "start_time", "end_time"],
    )

    op.create_table(
        "patient_booking_history",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("booking_id", sa.BigInteger(), nullable=False),
        sa.Column("old_date", sa.Date(), nullable=False),
        sa.Column("old_start_time", sa.Time(), nullable=False),
        sa.Column("old_end_time", sa.Time(), nullable=False),
        sa.Column("new_date", sa.Date(), nullable=False),
        sa.Column("new_start_time", sa.Time(), nullable=False),
        sa.Column("new_end_time", sa.Time(), nullable=False),
        sa.Column(
            "action",
            sa.String(length=50),
            nullable=False,
            server_default="RESCHEDULED",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(
            ["booking_id"],
            ["patient_bookings.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_patient_booking_history_booking_id",
        "patient_booking_history",
        ["booking_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_patient_booking_history_booking_id",
        table_name="patient_booking_history",
    )
    op.drop_table("patient_booking_history")

    op.drop_index(
        "ix_patient_bookings_date_time",
        table_name="patient_bookings",
    )
    op.drop_index(
        "ix_patient_bookings_status",
        table_name="patient_bookings",
    )
    op.drop_index(
        "ix_patient_bookings_booking_date",
        table_name="patient_bookings",
    )
    op.drop_index(
        "ix_patient_bookings_patient_id",
        table_name="patient_bookings",
    )
    op.drop_table("patient_bookings")
