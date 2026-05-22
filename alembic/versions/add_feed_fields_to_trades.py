"""add_feed_fields_to_trades

Revision ID: feed_fields_001
Revises: 93a5a2d475a4
Create Date: 2026-02-01 15:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'feed_fields_001'
down_revision: Union[str, None] = '93a5a2d475a4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add feed-specific columns to trades table
    op.add_column('trades', sa.Column('post_type', sa.String(), nullable=False, server_default='TRADE'))
    op.add_column('trades', sa.Column('hero_image_url', sa.Text(), nullable=True))
    op.add_column('trades', sa.Column('country', sa.String(length=2), nullable=False, server_default='US'))
    op.add_column('trades', sa.Column('region', sa.String(length=50), nullable=False, server_default='US-East'))
    op.add_column('trades', sa.Column('domestic_only', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('trades', sa.Column('quality_score', sa.Integer(), nullable=True))
    op.add_column('trades', sa.Column('view_count', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('trades', sa.Column('last_bumped_at', sa.DateTime(timezone=True), nullable=True))
    
    # Add check constraint for post_type
    op.create_check_constraint(
        'trades_post_type_check',
        'trades',
        "post_type IN ('TRADE', 'SALE', 'WTB')"
    )
    
    # Backfill last_bumped_at with created_at for existing records
    op.execute("UPDATE trades SET last_bumped_at = created_at WHERE last_bumped_at IS NULL")
    
    # Backfill hero_image_url from first offered card's image
    # This SQL finds the first offered item's card image for each trade
    op.execute("""
        UPDATE trades t
        SET hero_image_url = (
            SELECT c.image_url
            FROM trade_items ti
            JOIN cards c ON c.id = ti.card_id
            WHERE ti.trade_id = t.id
            AND ti.side = 'offer'
            AND c.image_url IS NOT NULL
            ORDER BY ti.created_at
            LIMIT 1
        )
        WHERE t.hero_image_url IS NULL
    """)
    
    # Fallback: If no offered card has image, try wanted cards
    op.execute("""
        UPDATE trades t
        SET hero_image_url = (
            SELECT c.image_url
            FROM trade_items ti
            JOIN cards c ON c.id = ti.card_id
            WHERE ti.trade_id = t.id
            AND ti.side = 'want'
            AND c.image_url IS NOT NULL
            ORDER BY ti.created_at
            LIMIT 1
        )
        WHERE t.hero_image_url IS NULL
    """)


def downgrade() -> None:
    # Remove check constraint
    op.drop_constraint('trades_post_type_check', 'trades', type_='check')
    
    # Remove columns
    op.drop_column('trades', 'last_bumped_at')
    op.drop_column('trades', 'view_count')
    op.drop_column('trades', 'quality_score')
    op.drop_column('trades', 'domestic_only')
    op.drop_column('trades', 'region')
    op.drop_column('trades', 'country')
    op.drop_column('trades', 'hero_image_url')
    op.drop_column('trades', 'post_type')

