"""add_performance_indexes

Revision ID: 7cb92b21caa4
Revises: 
Create Date: 2026-01-04 00:36:31.271135+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7cb92b21caa4'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add performance indexes for monthly statistics queries."""
    # Composite index for monthly aggregations (user_id + month)
    # Optimizes: SELECT ... WHERE user_id = X AND created_at >= 'YYYY-MM-01' AND created_at < 'YYYY-MM+1-01'
    op.create_index(
        'idx_emotions_user_month',
        'emotions',
        ['user_id', sa.text("DATE_TRUNC('month', created_at)")],
        postgresql_using='btree'
    )

    # Index for sorting by created_at DESC (most recent first)
    # Optimizes: ORDER BY created_at DESC queries
    op.create_index(
        'idx_emotions_created_desc',
        'emotions',
        [sa.text('created_at DESC')],
        postgresql_using='btree'
    )

    # Composite index for emotion type queries with timestamp
    # Optimizes: SELECT ... WHERE emotion = X AND created_at >= Y
    op.create_index(
        'idx_emotions_type_created',
        'emotions',
        ['emotion', 'created_at'],
        postgresql_using='btree'
    )


def downgrade() -> None:
    """Remove performance indexes."""
    op.drop_index('idx_emotions_type_created', table_name='emotions')
    op.drop_index('idx_emotions_created_desc', table_name='emotions')
    op.drop_index('idx_emotions_user_month', table_name='emotions')
