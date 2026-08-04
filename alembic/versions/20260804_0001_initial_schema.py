"""Initial Week 1-4 application schema.

Revision ID: 20260804_0001
Revises:
Create Date: 2026-08-04
"""

import app.models.model_registry  # noqa: F401
from alembic import op
from app.models.base import Base

revision = "20260804_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    Base.metadata.create_all(bind=op.get_bind(), checkfirst=True)


def downgrade() -> None:
    Base.metadata.drop_all(bind=op.get_bind(), checkfirst=True)
