"""Move factlabel_json out of hubfiles into a domain table (hubfile_factlabel).

Part of the hub/domain separation: the generic ``hubfiles`` table no longer
carries UVL-domain fact-label payloads. They move to ``hubfile_factlabel``,
keyed 1:1 by hubfile_id. Data is copied before the column is dropped.

Revision ID: f1a2b3c4d5e6
Revises: d1e2f3a4b5c6
Create Date: 2026-06-24
"""

import sqlalchemy as sa
from alembic import op

revision = "f1a2b3c4d5e6"
down_revision = "d1e2f3a4b5c6"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "hubfile_factlabel",
        sa.Column("hubfile_id", sa.Integer(), nullable=False),
        sa.Column("factlabel_json", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["hubfile_id"], ["hubfiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("hubfile_id"),
    )
    # Data-preserving copy of every existing fact label into the domain table.
    op.execute(
        "INSERT INTO hubfile_factlabel (hubfile_id, factlabel_json) "
        "SELECT id, factlabel_json FROM hubfiles WHERE factlabel_json IS NOT NULL"
    )
    op.drop_column("hubfiles", "factlabel_json")


def downgrade():
    op.add_column("hubfiles", sa.Column("factlabel_json", sa.Text(), nullable=True))
    op.execute(
        "UPDATE hubfiles h "
        "JOIN hubfile_factlabel f ON f.hubfile_id = h.id "
        "SET h.factlabel_json = f.factlabel_json"
    )
    op.drop_table("hubfile_factlabel")
