"""Add directory_path to hubfile (folder hierarchy within a dataset)."""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "a1b2c3d4e5f6"
down_revision = "69b397b5322b"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "hubfiles",
        sa.Column("directory_path", sa.String(255), nullable=False, server_default=""),
    )


def downgrade():
    op.drop_column("hubfiles", "directory_path")
