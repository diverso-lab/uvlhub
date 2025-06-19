"""change_email_user_to_nullable

Revision ID: 005
Revises: 004
Create Date: 2024-07-19 08:21:09.371820

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '005'
down_revision = '004'
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column('user', 'email',
               existing_type=sa.String(length=256),
               nullable=True)


def downgrade():
    op.alter_column('user', 'email',
               existing_type=sa.String(length=256),
               nullable=False)
