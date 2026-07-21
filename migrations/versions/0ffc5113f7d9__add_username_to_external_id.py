"""Add provider_username to external_identity."""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0ffc5113f7d9'
down_revision = '9914935ef33e'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('external_identity', sa.Column('provider_username', sa.String(256), nullable=True))


def downgrade():
    op.drop_column('external_identity', 'provider_username')
