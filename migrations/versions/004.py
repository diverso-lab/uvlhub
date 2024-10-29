"""add_orcid_table

Revision ID: 004
Revises: 003
Create Date: 2024-07-19 08:00:03.286457

"""
from alembic import op
import pytz
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector
from datetime import datetime

# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None

def upgrade():
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)

    if 'orcid' not in inspector.get_table_names():
        op.create_table(
            'orcid',
            sa.Column('id', sa.Integer, primary_key=True),
            sa.Column('orcid_id', sa.String(19), unique=True, nullable=False),
            sa.Column('registration_date', sa.DateTime, nullable=False, default=lambda: datetime.now(pytz.utc))
        )


def downgrade():
    op.drop_table('orcid')
