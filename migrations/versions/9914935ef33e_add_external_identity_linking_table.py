"""add external identity linking table

Revision ID: 9914935ef33e
Revises: fbc6e80289a7
Create Date: 2026-07-21 09:59:42.270335

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '9914935ef33e'
down_revision = 'fbc6e80289a7'
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'external_identity',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('provider', sa.String(50), nullable=False),
        sa.Column('provider_id', sa.String(256), nullable=False),
        sa.Column('email', sa.String(256), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['user.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('provider', 'provider_id', name='uq_provider_id')
    )
    op.create_index('ix_external_identity_user_id', 'external_identity', ['user_id'])


def downgrade():
    op.drop_index('ix_external_identity_user_id', table_name='external_identity')
    op.drop_table('external_identity')
