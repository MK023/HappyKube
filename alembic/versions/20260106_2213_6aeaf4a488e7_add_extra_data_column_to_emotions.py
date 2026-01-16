"""add_extra_data_column_to_emotions

Revision ID: 6aeaf4a488e7
Revises: 7cb92b21caa4
Create Date: 2026-01-06 22:13:31.578334+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6aeaf4a488e7'
down_revision: Union[str, Sequence[str], None] = '7cb92b21caa4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add extra_data column to emotions table (JSONB for PostgreSQL)
    # Using PostgreSQL's IF NOT EXISTS for idempotent migration
    op.execute("""
        ALTER TABLE emotions
        ADD COLUMN IF NOT EXISTS extra_data JSONB;
    """)


def downgrade() -> None:
    """Downgrade schema."""
    # Remove extra_data column from emotions table
    # Using PostgreSQL's IF EXISTS for idempotent migration
    op.execute("""
        ALTER TABLE emotions
        DROP COLUMN IF EXISTS extra_data;
    """)
