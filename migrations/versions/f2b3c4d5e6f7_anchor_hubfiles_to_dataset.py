"""Anchor hubfiles to their dataset directly (additive).

Part of the hub/domain separation: a hubfile (generic file) gains a direct
``dataset_id`` link to its container, so generic queries no longer need to go
through the UVL-domain ``feature_model``. This is additive — ``feature_model_id``
is kept as the domain grouping link — so it is safe and (almost) reversible.

The new column is backfilled from the existing feature_model -> dataset link
before being made NOT NULL.

Revision ID: f2b3c4d5e6f7
Revises: f1a2b3c4d5e6
Create Date: 2026-06-24
"""

import sqlalchemy as sa
from alembic import op

revision = "f2b3c4d5e6f7"
down_revision = "f1a2b3c4d5e6"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("hubfiles", sa.Column("dataset_id", sa.Integer(), nullable=True))
    # Backfill the new direct link from the existing feature_model -> dataset path.
    op.execute(
        "UPDATE hubfiles h "
        "JOIN feature_model fm ON fm.id = h.feature_model_id "
        "SET h.dataset_id = fm.dataset_id"
    )
    op.alter_column("hubfiles", "dataset_id", existing_type=sa.Integer(), nullable=False)
    op.create_index("ix_hubfiles_dataset_id", "hubfiles", ["dataset_id"])
    op.create_foreign_key("fk_hubfiles_dataset_id", "hubfiles", "datasets", ["dataset_id"], ["id"])


def downgrade():
    op.drop_constraint("fk_hubfiles_dataset_id", "hubfiles", type_="foreignkey")
    op.drop_index("ix_hubfiles_dataset_id", table_name="hubfiles")
    op.drop_column("hubfiles", "dataset_id")
