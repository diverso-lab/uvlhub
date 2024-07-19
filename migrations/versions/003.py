from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector

# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None

def upgrade():
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)

    # Verificar si la columna ya existe en la tabla 'ds_meta_data'
    columns = [col['name'] for col in inspector.get_columns('ds_meta_data')]
    if 'dataset_anonymous' not in columns:
        with op.batch_alter_table('ds_meta_data', schema=None) as batch_op:
            batch_op.add_column(sa.Column('dataset_anonymous', sa.Boolean(), nullable=True))

def downgrade():
    with op.batch_alter_table('ds_meta_data', schema=None) as batch_op:
        batch_op.drop_column('dataset_anonymous')
