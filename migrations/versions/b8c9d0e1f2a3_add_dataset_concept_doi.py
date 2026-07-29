"""Add the Zenodo concept DOI to dataset metadata (additive).

Zenodo mints two identifiers for a deposition: the version DOI (``doi``) and
the concept DOI (``conceptdoi``), the permanent identifier of the whole
version lineage that always resolves to its newest version. Only the version
DOI was stored, so a client holding an old DOI could not discover newer
versions.

``ds_meta_data.dataset_concept_doi`` (nullable, indexed) stores it. Every
version of a lineage shares the same value. Existing rows keep NULL: records
published before this column existed, and depositions for which Zenodo returns
no conceptdoi, are still fully usable.

Revision ID: b8c9d0e1f2a3
Revises: a7c1d2e3f4b5
Create Date: 2026-07-26
"""

import sqlalchemy as sa
from alembic import op

revision = "b8c9d0e1f2a3"
down_revision = "a7c1d2e3f4b5"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("ds_meta_data", schema=None) as batch_op:
        batch_op.add_column(sa.Column("dataset_concept_doi", sa.String(length=120), nullable=True))
        batch_op.create_index(
            "ix_ds_meta_data_dataset_concept_doi",
            ["dataset_concept_doi"],
            unique=False,
        )


def downgrade():
    with op.batch_alter_table("ds_meta_data", schema=None) as batch_op:
        batch_op.drop_index("ix_ds_meta_data_dataset_concept_doi")
        batch_op.drop_column("dataset_concept_doi")
