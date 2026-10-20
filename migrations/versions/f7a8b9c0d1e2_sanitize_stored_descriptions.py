"""Clean the stored dataset descriptions through the description allowlist.

The web upload stored descriptions without sanitizing them, and the DOI landing
page, the home page and Explore print the description as HTML. New input is
sanitized now; this cleans the rows written before, so every copy of a
description (database and search index after a reindex) is safe to render.
"""
from alembic import op
import bleach
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "f7a8b9c0d1e2"
down_revision = "e5f6a7b8c9d0"
branch_labels = None
depends_on = None

# The allowlist of DataSetService.sanitize_description when this migration was
# written, copied here so the migration keeps doing the same thing if the
# service changes later.
ALLOWED_TAGS = ["p", "br", "strong", "em", "b", "i", "u", "ul", "ol", "li", "a"]
ALLOWED_ATTRIBUTES = {"a": ["href", "title", "target"]}


def _clean(description):
    return bleach.clean(description or "", tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES, strip=True).strip()


def upgrade():
    conn = op.get_bind()
    ds_meta_data = sa.table("ds_meta_data", sa.column("id", sa.Integer), sa.column("description", sa.Text))

    rows = conn.execute(sa.select(ds_meta_data.c.id, ds_meta_data.c.description)).fetchall()
    for row_id, description in rows:
        clean = _clean(description)
        if clean != description:
            conn.execute(ds_meta_data.update().where(ds_meta_data.c.id == row_id).values(description=clean))


def downgrade():
    # The markup removed by upgrade() is not kept anywhere, so there is nothing to restore.
    pass
