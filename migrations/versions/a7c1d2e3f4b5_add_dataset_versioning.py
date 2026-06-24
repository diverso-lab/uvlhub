"""Add dataset versioning / lineage columns (additive).

Replacing a UVL on a published dataset creates a new dataset (a new version)
that points at the one it was derived from. Two additive columns on ``datasets``
support this, mirroring Zenodo's concept-DOI version chain:

- ``dataset_version`` (int, default 1): the version number.
- ``dataset_origin_id`` (nullable self-FK): the previous version this one was
  derived from; NULL for originals.

Existing rows become version 1 with no origin, so this is data-preserving and
fully reversible.

Revision ID: a7c1d2e3f4b5
Revises: f2b3c4d5e6f7
Create Date: 2026-06-24
"""

import sqlalchemy as sa
from alembic import op

revision = "a7c1d2e3f4b5"
down_revision = "f2b3c4d5e6f7"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "datasets",
        sa.Column("dataset_version", sa.Integer(), nullable=False, server_default="1"),
    )
    op.add_column("datasets", sa.Column("dataset_origin_id", sa.Integer(), nullable=True))
    op.create_index("ix_datasets_dataset_origin_id", "datasets", ["dataset_origin_id"])
    op.create_foreign_key(
        "fk_datasets_dataset_origin_id", "datasets", "datasets", ["dataset_origin_id"], ["id"]
    )
    # Drop the server_default now that existing rows are backfilled; the model
    # supplies the default on insert.
    op.alter_column("datasets", "dataset_version", existing_type=sa.Integer(), server_default=None)


def downgrade():
    op.drop_constraint("fk_datasets_dataset_origin_id", "datasets", type_="foreignkey")
    op.drop_index("ix_datasets_dataset_origin_id", table_name="datasets")
    op.drop_column("datasets", "dataset_origin_id")
    op.drop_column("datasets", "dataset_version")
