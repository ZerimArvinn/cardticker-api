"""add_user_photos_to_trade_items

Revision ID: user_photos_001
Revises: feed_fields_001
Create Date: 2026-02-03 12:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'user_photos_001'
down_revision: Union[str, None] = 'feed_fields_001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add user_photos JSONB column to trade_items table
    # Format: [{"url": "https://...", "label": "Front"}, {"url": "https://...", "label": "Back"}]
    op.add_column('trade_items', sa.Column('user_photos', postgresql.JSONB(astext_type=sa.Text()), nullable=True))


def downgrade() -> None:
    # Remove user_photos column from trade_items table
    op.drop_column('trade_items', 'user_photos')

