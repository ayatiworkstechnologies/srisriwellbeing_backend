"""Add a human-readable name to permissions.

Revision ID: 20260811_0002
Revises: 20260804_0001
Create Date: 2026-08-11
"""

import sqlalchemy as sa
from alembic import op

revision = "20260811_0002"
down_revision = "20260804_0001"
branch_labels = None
depends_on = None


def _permission_columns() -> set[str]:
    inspector = sa.inspect(op.get_bind())
    return {
        column["name"]
        for column in inspector.get_columns("permissions")
    }


def upgrade() -> None:
    if "name" not in _permission_columns():
        op.add_column(
            "permissions",
            sa.Column("name", sa.String(length=150), nullable=True),
        )

    permissions = sa.table(
        "permissions",
        sa.column("name", sa.String(length=150)),
        sa.column("code", sa.String(length=200)),
    )
    op.execute(
        permissions.update()
        .where(permissions.c.name.is_(None))
        .values(name=permissions.c.code)
    )
    op.alter_column(
        "permissions",
        "name",
        existing_type=sa.String(length=150),
        nullable=False,
    )


def downgrade() -> None:
    if "name" in _permission_columns():
        op.drop_column("permissions", "name")
