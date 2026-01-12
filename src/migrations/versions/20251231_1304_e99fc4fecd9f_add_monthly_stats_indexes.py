"""add_monthly_stats_indexes

Revision ID: e99fc4fecd9f
Revises: 001
Create Date: 2025-12-31 13:04:15.308578+00:00

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'e99fc4fecd9f'
down_revision: str | None = '001'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add optimized indexes for monthly statistics queries.

    Key optimizations:
    1. Composite index on (user_id, created_at) for monthly range queries
    2. BRIN index on created_at for time-series data (space-efficient)
    3. Composite index on audit_log for compliance queries
    """

    # Drop old single-column created_at index (will be replaced by BRIN)
    op.drop_index('ix_emotions_created_at', table_name='emotions')

    # Add BRIN index for created_at (time-series data, space-efficient)
    # BRIN is perfect for sorted timestamp columns - uses ~1000x less space than B-tree
    op.execute("""
        CREATE INDEX ix_emotions_created_at_brin
        ON emotions USING BRIN (created_at)
    """)

    # Verify ix_emotions_user_created already exists (created in 001)
    # This is the critical index for: WHERE user_id = X AND created_at BETWEEN Y AND Z
    # Format: (user_id, created_at DESC) - perfect for monthly stats

    # Add composite index on audit_log for compliance queries
    # Query pattern: WHERE user_id = X AND created_at BETWEEN Y AND Z ORDER BY created_at DESC
    op.create_index(
        'ix_audit_log_user_created',
        'audit_log',
        ['user_id', sa.text('created_at DESC')],
        unique=False
    )

    # Add partial index for active users only (reduces index size)
    op.execute("""
        CREATE INDEX ix_users_active
        ON users (id)
        WHERE is_active = true
    """)


def downgrade() -> None:
    """Remove monthly statistics indexes."""

    # Remove partial index for active users
    op.execute('DROP INDEX IF EXISTS ix_users_active')

    # Remove audit_log composite index
    op.drop_index('ix_audit_log_user_created', table_name='audit_log')

    # Remove BRIN index
    op.execute('DROP INDEX IF EXISTS ix_emotions_created_at_brin')

    # Restore original B-tree index on created_at
    op.create_index('ix_emotions_created_at', 'emotions', ['created_at'], unique=False)
