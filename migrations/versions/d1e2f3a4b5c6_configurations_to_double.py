"""widen hubfile_metrics.configurations from BIGINT to DOUBLE

Real feature models routinely produce 2^N-scale configuration counts that
overflow BIGINT (signed max ~9.2e18). A 140-feature model with mostly
independent optional features reports ~1.27e30 configurations, which blows
up the INSERT. Double precision covers anything fmfactlabel can compute
at the cost of ~15 significant digits — fine for histograms and summaries,
and the `configurations_is_upper_bound` flag still captures any analytic
uncertainty.

Revision ID: d1e2f3a4b5c6
Revises: c7d8e9f0a1b2
Create Date: 2026-04-23 15:00:00.000000

"""
import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = "d1e2f3a4b5c6"
down_revision = "c7d8e9f0a1b2"
branch_labels = None
depends_on = None


def upgrade():
    # `Float(precision=53)` renders as DOUBLE on MySQL/MariaDB and REAL
    # (already 8-byte IEEE 754) on SQLite, so the migration is portable
    # between the prod DB and the in-process test DB.
    with op.batch_alter_table("hubfile_metrics", schema=None) as batch_op:
        batch_op.alter_column(
            "configurations",
            existing_type=sa.BigInteger(),
            type_=sa.Float(precision=53),
            existing_nullable=True,
        )


def downgrade():
    # Downgrade would silently truncate any value that doesn't fit in BIGINT,
    # so keep it honest: cast through, let MariaDB drop the over-range rows
    # rather than lie about the data.
    with op.batch_alter_table("hubfile_metrics", schema=None) as batch_op:
        batch_op.alter_column(
            "configurations",
            existing_type=sa.Float(precision=53),
            type_=sa.BigInteger(),
            existing_nullable=True,
        )
