"""add metadata_synced flag

Revision ID: b3f9e4c2a1d0
Revises: 976920761330
Create Date: 2026-04-07 02:15:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b3f9e4c2a1d0'
down_revision = '976920761330'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('ds_meta_data', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                'metadata_synced',
                sa.Boolean(),
                nullable=False,
                server_default=sa.true(),
            )
        )


def downgrade():
    with op.batch_alter_table('ds_meta_data', schema=None) as batch_op:
        batch_op.drop_column('metadata_synced')
