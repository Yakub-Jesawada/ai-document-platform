"""add embedding field and related flags

Revision ID: 9af903e57689
Revises: 3f9252c83b2c
Create Date: 2026-02-04 20:00:27.520456

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import pgvector


# revision identifiers, used by Alembic.
revision: str = '9af903e57689'
down_revision: Union[str, Sequence[str], None] = '3f9252c83b2c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.add_column(
        "document_chunks",
        sa.Column(
            "embedding",
            pgvector.sqlalchemy.vector.VECTOR(dim=384),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("document_chunks", "embedding")
    # usually you DON'T drop the extension in downgrade

