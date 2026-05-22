"""add cognito_sub to users

Revision ID: cognito_sub_001
Revises: user_photos_001
Create Date: 2026-02-04 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'cognito_sub_001'
down_revision = 'user_photos_001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add cognito_sub column to users table
    op.add_column('users', sa.Column('cognito_sub', sa.String(), nullable=True))
    op.create_index(op.f('ix_users_cognito_sub'), 'users', ['cognito_sub'], unique=True)


def downgrade() -> None:
    # Remove cognito_sub column
    op.drop_index(op.f('ix_users_cognito_sub'), table_name='users')
    op.drop_column('users', 'cognito_sub')

