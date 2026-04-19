"""add datasets_counter and feature_models_counter to statistics

Revision ID: 976920761330
Revises: 8a96e53e7e32
Create Date: 2026-04-16 00:20:30.042768

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '976920761330'
down_revision = '8a96e53e7e32'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('statistics', schema=None) as batch_op:
        batch_op.add_column(sa.Column('datasets_counter', sa.Integer(), nullable=True, server_default='0'))
        batch_op.add_column(sa.Column('feature_models_counter', sa.Integer(), nullable=True, server_default='0'))


def downgrade():
    with op.batch_alter_table('statistics', schema=None) as batch_op:
        batch_op.drop_column('feature_models_counter')
        batch_op.drop_column('datasets_counter')
