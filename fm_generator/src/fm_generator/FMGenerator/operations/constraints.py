import random

from flamapy.core.models.ast import AST
from flamapy.metamodels.fm_metamodel.models.feature_model import (
    Constraint,
    Feature,
    FeatureModel,
)

from fm_generator.FMGenerator.models.config import Params
from fm_generator.FMGenerator.operations.constraint_pools import (
    build_constraint_pools,
    constraints_must_be_boolean_only,
)
from fm_generator.FMGenerator.operations.constraint_predicates import (
    build_boolean_predicate,
    build_mixed_constraint,
)
from fm_generator.FMGenerator.operations.constraint_sampling import (
    ensure_non_empty_filtered_pool,
    filter_attrs_for_constraint,
    filter_len_groups_for_numeric_use,
    group_keys_by_feature,
    max_occurrences_possible,
    sample_keys_with_ecr,
)


def add_constraints(
    fm: FeatureModel,
    features: list[Feature],
    params: Params,
) -> None:
    boolean_only_constraints = constraints_must_be_boolean_only(params)

    (
        feats_bool,
        feats_num,
        feats_str,
        attrs_bool,
        attrs_num,
        attrs_str,
    ) = build_constraint_pools(features, params)

    min_vars = int(getattr(params, "MIN_VARS_PER_CONSTRAINT", 1))
    max_vars = int(getattr(params, "MAX_VARS_PER_CONSTRAINT", 2))

    min_vars = max(1, min_vars)
    max_vars = max(1, max_vars)

    if min_vars > max_vars:
        min_vars = max_vars

    max_reps = int(getattr(params, "EXTRA_CONSTRAINT_REPRESENTATIVENESS", 1))
    max_reps = max(1, max_reps)
    max_reps = min(max_reps, max_vars)

    max_features_param = int(getattr(params, "MAX_FEATURES", 10))
    max_features_param = max(1, max_features_param)

    total_ctcs = random.randint(params.MIN_CONSTRAINTS, params.MAX_CONSTRAINTS)

    for i in range(total_ctcs):
        filtered_bool_attrs = ensure_non_empty_filtered_pool(
            filter_attrs_for_constraint(attrs_bool),
            attrs_bool,
        )
        filtered_num_attrs = ensure_non_empty_filtered_pool(
            filter_attrs_for_constraint(attrs_num),
            attrs_num,
        )
        filtered_str_attrs = ensure_non_empty_filtered_pool(
            filter_attrs_for_constraint(attrs_str),
            attrs_str,
        )

        bool_pool = [feature.name for feature in feats_bool] + [
            f"{feature.name}.{attr.name}" for feature, attr in filtered_bool_attrs
        ]
        num_pool = [feature.name for feature in feats_num] + [
            f"{feature.name}.{attr.name}" for feature, attr in filtered_num_attrs
        ]
        str_pool = [feature.name for feature in feats_str] + [
            f"{feature.name}.{attr.name}" for feature, attr in filtered_str_attrs
        ]

        bool_groups = group_keys_by_feature(list(set(bool_pool)))
        num_groups = group_keys_by_feature(list(set(num_pool)))
        str_groups = group_keys_by_feature(list(set(str_pool)))

        len_prob = float(getattr(params, "PROB_LEN_FUNCTION", 0.0))

        len_pool = []
        if (
            not boolean_only_constraints
            and getattr(params, "TYPE_LEVEL", False)
            and getattr(params, "STRING_CONSTRAINTS", False)
        ):
            len_pool.extend([feature.name for feature in feats_str])
            len_pool.extend(f"{feature.name}.{attr.name}" for feature, attr in filtered_str_attrs)

        len_groups = group_keys_by_feature(list(set(len_pool)))
        numeric_len_groups = filter_len_groups_for_numeric_use(len_groups, len_prob)

        total_capacity = 0

        if bool_groups:
            total_capacity += max_occurrences_possible(
                bool_groups,
                max_features_param,
                max_reps,
            )
        if num_groups:
            total_capacity += max_occurrences_possible(
                num_groups,
                max_features_param,
                max_reps,
            )
        if str_groups:
            total_capacity += max_occurrences_possible(
                str_groups,
                max_features_param,
                max_reps,
            )
        if numeric_len_groups:
            total_capacity += max_occurrences_possible(
                numeric_len_groups,
                max_features_param,
                max_reps,
            )

        effective_max = min(max_vars, total_capacity)
        effective_min = min_vars

        if effective_max < effective_min:
            continue

        target_occ = random.randint(effective_min, effective_max)

        if boolean_only_constraints:
            if not bool_groups:
                continue

            bool_capacity = max_occurrences_possible(
                bool_groups,
                max_features_param,
                max_reps,
            )
            effective_max = min(max_vars, bool_capacity)
            effective_min = min_vars

            if effective_max < effective_min:
                continue

            target_occ = random.randint(effective_min, effective_max)
            chosen = sample_keys_with_ecr(
                bool_groups,
                target_occ,
                max_reps,
                max_features_param,
            )

            if not chosen:
                continue

            root = build_boolean_predicate(chosen, params)
        else:
            root = build_mixed_constraint(
                bool_groups,
                num_groups,
                str_groups,
                numeric_len_groups,
                target_occ,
                params,
                max_reps,
                max_features_param,
            )

        if root is None:
            continue

        fm.ctcs.append(Constraint(name=f"ctc{i}", ast=AST(root)))
