"""add hubfile_metrics table

Revision ID: c7d8e9f0a1b2
Revises: b3f9e4c2a1d0
Create Date: 2026-04-23 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c7d8e9f0a1b2'
down_revision = 'b3f9e4c2a1d0'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'hubfile_metrics',
        sa.Column('hubfile_id', sa.Integer(), nullable=False),
        sa.Column('extracted_at', sa.DateTime(), nullable=False),
        sa.Column('extractor_version', sa.String(length=20), nullable=False),
        sa.Column('parse_error', sa.Text(), nullable=True),

        # Structural — features
        sa.Column('features', sa.Integer(), nullable=True),
        sa.Column('abstract_features', sa.Integer(), nullable=True),
        sa.Column('concrete_features', sa.Integer(), nullable=True),
        sa.Column('leaf_features', sa.Integer(), nullable=True),
        sa.Column('compound_features', sa.Integer(), nullable=True),
        sa.Column('top_features', sa.Integer(), nullable=True),
        sa.Column('solitary_features', sa.Integer(), nullable=True),
        sa.Column('grouped_features', sa.Integer(), nullable=True),
        sa.Column('typed_features', sa.Integer(), nullable=True),
        sa.Column('multi_features', sa.Integer(), nullable=True),

        # Structural — relationships
        sa.Column('tree_relationships', sa.Integer(), nullable=True),
        sa.Column('mandatory_features', sa.Integer(), nullable=True),
        sa.Column('optional_features', sa.Integer(), nullable=True),
        sa.Column('feature_groups', sa.Integer(), nullable=True),
        sa.Column('alternative_groups', sa.Integer(), nullable=True),
        sa.Column('or_groups', sa.Integer(), nullable=True),
        sa.Column('mutex_groups', sa.Integer(), nullable=True),
        sa.Column('cardinality_groups', sa.Integer(), nullable=True),

        # Structural — tree shape
        sa.Column('depth_of_tree', sa.Integer(), nullable=True),
        sa.Column('mean_depth_of_tree', sa.Float(), nullable=True),
        sa.Column('branching_factor', sa.Float(), nullable=True),
        sa.Column('min_children_per_feature', sa.Integer(), nullable=True),
        sa.Column('max_children_per_feature', sa.Integer(), nullable=True),
        sa.Column('avg_children_per_feature', sa.Float(), nullable=True),

        # Structural — constraints
        sa.Column('cross_tree_constraints', sa.Integer(), nullable=True),
        sa.Column('logical_constraints', sa.Integer(), nullable=True),
        sa.Column('simple_constraints', sa.Integer(), nullable=True),
        sa.Column('requires_constraints', sa.Integer(), nullable=True),
        sa.Column('excludes_constraints', sa.Integer(), nullable=True),
        sa.Column('complex_constraints', sa.Integer(), nullable=True),
        sa.Column('pseudo_complex_constraints', sa.Integer(), nullable=True),
        sa.Column('strict_complex_constraints', sa.Integer(), nullable=True),
        sa.Column('arithmetic_constraints', sa.Integer(), nullable=True),
        sa.Column('aggregation_constraints', sa.Integer(), nullable=True),
        sa.Column('features_in_constraints', sa.Integer(), nullable=True),
        sa.Column('avg_features_per_constraint', sa.Float(), nullable=True),
        sa.Column('avg_constraints_per_feature', sa.Float(), nullable=True),

        # Semantic
        sa.Column('satisfiable', sa.Boolean(), nullable=True),
        sa.Column('core_features', sa.Integer(), nullable=True),
        sa.Column('false_optional_features', sa.Integer(), nullable=True),
        sa.Column('dead_features', sa.Integer(), nullable=True),
        sa.Column('variant_features', sa.Integer(), nullable=True),
        sa.Column('unique_features', sa.Integer(), nullable=True),
        sa.Column('pure_optional_features', sa.Integer(), nullable=True),
        sa.Column('configurations', sa.BigInteger(), nullable=True),
        sa.Column('configurations_is_upper_bound', sa.Boolean(), nullable=True),
        sa.Column('total_variability', sa.Float(), nullable=True),
        sa.Column('partial_variability', sa.Float(), nullable=True),
        sa.Column('homogeneity', sa.Float(), nullable=True),
        sa.Column('cfg_mean_features', sa.Float(), nullable=True),
        sa.Column('cfg_stddev_features', sa.Float(), nullable=True),
        sa.Column('cfg_median_features', sa.Float(), nullable=True),
        sa.Column('cfg_min_features', sa.Integer(), nullable=True),
        sa.Column('cfg_max_features', sa.Integer(), nullable=True),

        sa.ForeignKeyConstraint(['hubfile_id'], ['hubfiles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('hubfile_id'),
    )

    # Index on the most common dashboard filters: skip rows whose extraction
    # failed (parse_error IS NOT NULL) and bucket by satisfiability.
    op.create_index('ix_hubfile_metrics_satisfiable', 'hubfile_metrics', ['satisfiable'])
    op.create_index('ix_hubfile_metrics_features', 'hubfile_metrics', ['features'])


def downgrade():
    op.drop_index('ix_hubfile_metrics_features', table_name='hubfile_metrics')
    op.drop_index('ix_hubfile_metrics_satisfiable', table_name='hubfile_metrics')
    op.drop_table('hubfile_metrics')
