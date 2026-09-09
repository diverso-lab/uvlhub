"""Add dataset_rating table (👍/👎 dataset ratings)."""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "e5f6a7b8c9d0"
down_revision = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "dataset_rating",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("dataset_id", sa.Integer(), nullable=False),
        sa.Column("is_like", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["dataset_id"], ["datasets.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "dataset_id", name="uq_rating_user_dataset"),
    )
    op.create_index(op.f("ix_dataset_rating_user_id"), "dataset_rating", ["user_id"])
    op.create_index(op.f("ix_dataset_rating_dataset_id"), "dataset_rating", ["dataset_id"])


def downgrade():
    op.drop_index(op.f("ix_dataset_rating_dataset_id"), table_name="dataset_rating")
    op.drop_index(op.f("ix_dataset_rating_user_id"), table_name="dataset_rating")
    op.drop_table("dataset_rating")
