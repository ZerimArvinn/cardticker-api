"""add viewed_at to proposals

Revision ID: viewed_at_001
Revises: cognito_sub_001
Create Date: 2026-02-04 15:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'viewed_at_001'
down_revision = 'cognito_sub_001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add viewed_at column to trade_proposals table
    op.add_column('trade_proposals', sa.Column('viewed_at', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    # Remove viewed_at column
    op.drop_column('trade_proposals', 'viewed_at')

