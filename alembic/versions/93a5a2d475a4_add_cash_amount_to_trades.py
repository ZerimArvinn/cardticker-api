"""add_cash_amount_to_trades

Revision ID: 93a5a2d475a4
Revises: 02fc3313c04f
Create Date: 2026-02-01 08:39:34.739426

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '93a5a2d475a4'
down_revision: Union[str, None] = '02fc3313c04f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add cash_amount_cents column to trades table
    op.add_column('trades', sa.Column('cash_amount_cents', sa.Integer(), nullable=True))


def downgrade() -> None:
    # Remove cash_amount_cents column from trades table
    op.drop_column('trades', 'cash_amount_cents')

