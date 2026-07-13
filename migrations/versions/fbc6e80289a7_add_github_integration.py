"""Create github table for GitHub OAuth integration.

Revision ID: fbc6e80289a7
Revises: a7c1d2e3f4b5
Create Date: 2026-07-09
"""
from alembic import op
import sqlalchemy as sa

revision = "fbc6e80289a7"
down_revision = "a7c1d2e3f4b5"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('github',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('github_id', sa.Integer(), nullable=False),
        sa.Column('github_login', sa.String(length=255), nullable=False),
        sa.Column('registration_date', sa.DateTime(), nullable=False),
        sa.Column('profile_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['profile_id'], ['user_profile.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('github_id'),
        sa.UniqueConstraint('profile_id')
    )
    op.create_index('ix_github_github_id', 'github', ['github_id'], unique=True)
    op.create_index('ix_github_profile_id', 'github', ['profile_id'], unique=True)


def downgrade():
    op.drop_index('ix_github_profile_id', table_name='github')
    op.drop_index('ix_github_github_id', table_name='github')
    op.drop_table('github')