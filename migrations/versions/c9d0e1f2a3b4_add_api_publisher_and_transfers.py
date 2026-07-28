"""Record who published through the API and gate ownership transfers (additive).

Two independent gaps in the API surface, both about attribution:

- ``ds_meta_data.api_publisher_user_id`` (nullable FK to ``user``): the account
  whose API key created the record. Author credit sent by an API client is a
  claim about somebody else, and the dataset's ``user_id`` stops answering the
  question once ownership is transferred, so the publisher is recorded
  separately and published in the Zenodo record's notes. NULL for everything
  created through the web interface and for every existing row.

- ``dataset_transfer_request``: an offer to hand a dataset lineage to another
  account, pending that account's answer. Ownership used to move on the
  sender's word alone, which let a key holder drop a permanent public record on
  somebody who never asked for it. Nothing moves until the row reaches the
  ``ACCEPTED`` status.

Both additions are data-preserving and fully reversible.

Revision ID: c9d0e1f2a3b4
Revises: b8c9d0e1f2a3
Create Date: 2026-07-26
"""

import sqlalchemy as sa
from alembic import op

revision = "c9d0e1f2a3b4"
down_revision = "b8c9d0e1f2a3"
branch_labels = None
depends_on = None

TRANSFER_STATUS = sa.Enum(
    "PENDING",
    "ACCEPTED",
    "DECLINED",
    "CANCELLED",
    name="datasettransferstatus",
)


def upgrade():
    with op.batch_alter_table("ds_meta_data", schema=None) as batch_op:
        batch_op.add_column(sa.Column("api_publisher_user_id", sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            "fk_ds_meta_data_api_publisher_user_id",
            "user",
            ["api_publisher_user_id"],
            ["id"],
        )

    op.create_table(
        "dataset_transfer_request",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("dataset_id", sa.Integer(), nullable=False),
        sa.Column("from_user_id", sa.Integer(), nullable=False),
        sa.Column("to_user_id", sa.Integer(), nullable=False),
        sa.Column("status", TRANSFER_STATUS, nullable=False),
        sa.Column("message", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("resolved_at", sa.DateTime(), nullable=True),
        # An offer cannot outlive the dataset it offers. Without the cascade
        # the constraint refuses every deletion of a dataset that has ever been
        # offered, which breaks the admin cleanup command permanently.
        sa.ForeignKeyConstraint(["dataset_id"], ["datasets.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["from_user_id"], ["user.id"]),
        sa.ForeignKeyConstraint(["to_user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_dataset_transfer_request_dataset_id",
        "dataset_transfer_request",
        ["dataset_id"],
    )
    op.create_index(
        "ix_dataset_transfer_request_from_user_id",
        "dataset_transfer_request",
        ["from_user_id"],
    )
    op.create_index(
        "ix_dataset_transfer_request_to_user_id",
        "dataset_transfer_request",
        ["to_user_id"],
    )


def downgrade():
    # The indexes are not dropped one by one on purpose. MySQL/MariaDB back
    # every foreign key with an index and refuse to drop it while the
    # constraint exists ("Cannot drop index ...: needed in a foreign key
    # constraint", error 1553), which made this downgrade fail halfway.
    # Dropping the table takes its indexes with it.
    op.drop_table("dataset_transfer_request")
    TRANSFER_STATUS.drop(op.get_bind(), checkfirst=True)

    with op.batch_alter_table("ds_meta_data", schema=None) as batch_op:
        batch_op.drop_constraint("fk_ds_meta_data_api_publisher_user_id", type_="foreignkey")
        batch_op.drop_column("api_publisher_user_id")
