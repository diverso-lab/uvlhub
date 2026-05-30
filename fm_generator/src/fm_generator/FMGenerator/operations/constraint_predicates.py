import random

from flamapy.core.models.ast import ASTOperation, Node

from fm_generator.FMGenerator.models.config import Params
from fm_generator.FMGenerator.operations.constraint_sampling import sample_keys_with_ecr

# -----------------------------
# Boolean helpers
# -----------------------------


def pick_bool_op(params: Params) -> ASTOperation:
    ops = [
        ASTOperation.AND,
        ASTOperation.OR,
        ASTOperation.IMPLIES,
        ASTOperation.EQUIVALENCE,
    ]
    weights = [
        float(getattr(params, "PROB_AND", 0.7)),
        float(getattr(params, "PROB_OR_CT", 0.1)),
        float(getattr(params, "PROB_IMPLICATION", 0.1)),
        float(getattr(params, "PROB_EQUIVALENCE", 0.1)),
    ]

    return random.choices(ops, weights=weights, k=1)[0]


def maybe_not(node: Node, params: Params) -> Node:
    if random.random() < float(getattr(params, "PROB_NOT", 0.0)):
        return Node(ASTOperation.NOT, node)
    return node


def build_left_deep_bool_ast(nodes: list[Node], params: Params) -> Node:
    """Build (((n1 op n2) op n3) op n4) ..."""
    assert len(nodes) >= 2

    cur = Node(pick_bool_op(params), nodes[0], nodes[1])
    for node in nodes[2:]:
        cur = Node(pick_bool_op(params), cur, node)

    return cur


def build_boolean_predicate(keys: list[str], params: Params) -> Node | None:
    if not keys:
        return None

    literals = [maybe_not(Node(key), params) for key in keys]

    if len(literals) == 1:
        return literals[0]

    return build_left_deep_bool_ast(literals, params)


# -----------------------------
# Numeric / arithmetic helpers
# -----------------------------


def pick_binary_arith_op(params: Params) -> ASTOperation:
    ops = [
        ASTOperation.ADD,
        ASTOperation.SUB,
        ASTOperation.MUL,
        ASTOperation.DIV,
    ]
    weights = [
        float(getattr(params, "PROB_SUM", 0.7)),
        float(getattr(params, "PROB_SUBSTRACT", 0.2)),
        float(getattr(params, "PROB_MULTIPLY", 0.1)),
        float(getattr(params, "PROB_DIVIDE", 0.0)),
    ]

    if sum(weights) <= 0.0:
        return ASTOperation.ADD

    return random.choices(ops, weights=weights, k=1)[0]


def pick_cmp_op(params: Params) -> ASTOperation:
    ops = [
        ASTOperation.EQUALS,
        ASTOperation.LOWER,
        ASTOperation.GREATER,
        ASTOperation.LOWER_EQUALS,
        ASTOperation.GREATER_EQUALS,
    ]
    weights = [
        float(getattr(params, "PROB_EQUALS", 0.1)),
        float(getattr(params, "PROB_LESS", 0.2)),
        float(getattr(params, "PROB_GREATER", 0.7)),
        float(getattr(params, "PROB_LESS_EQUALS", 0.0)),
        float(getattr(params, "PROB_GREATER_EQUALS", 0.0)),
    ]

    return random.choices(ops, weights=weights, k=1)[0]


def pick_aggregate_name(params: Params) -> str | None:
    if not getattr(params, "AGGREGATE_FUNCTIONS", False):
        return None

    prob_sum_function = float(getattr(params, "PROB_SUM_FUNCTION", 0.0))
    prob_avg_function = float(getattr(params, "PROB_AVG_FUNCTION", 0.0))

    total = prob_sum_function + prob_avg_function
    if total <= 0.0:
        return None

    return random.choices(
        ["sum", "avg"],
        weights=[prob_sum_function, prob_avg_function],
        k=1,
    )[0]


def build_function_node(func_name: str, keys: list[str]) -> Node:
    args = ", ".join(keys)
    return Node(f"{func_name}({args})")


def maybe_wrap_key_with_len(key: str, len_eligible_keys: set[str]) -> str:
    if key in len_eligible_keys:
        return f"len({key})"
    return key


def build_function_style_node(expr: str) -> Node:
    return Node(expr)


def build_plain_arith_expr(
    keys: list[str],
    params: Params,
    len_eligible_keys: set[str] | None = None,
) -> Node:
    len_eligible_keys = len_eligible_keys or set()

    first_key = maybe_wrap_key_with_len(keys[0], len_eligible_keys)
    cur = build_function_style_node(first_key)

    for key in keys[1:]:
        wrapped_key = maybe_wrap_key_with_len(key, len_eligible_keys)
        cur = Node(
            pick_binary_arith_op(params),
            cur,
            build_function_style_node(wrapped_key),
        )

    return cur


def maybe_wrap_with_aggregate(
    expr: Node,
    keys: list[str],
    params: Params,
    len_eligible_keys: set[str] | None = None,
) -> Node:
    len_eligible_keys = len_eligible_keys or set()

    if not getattr(params, "AGGREGATE_FUNCTIONS", False):
        return expr

    if len(keys) < 2:
        return expr

    prob_sum_function = float(getattr(params, "PROB_SUM_FUNCTION", 0.0))
    prob_avg_function = float(getattr(params, "PROB_AVG_FUNCTION", 0.0))
    aggregate_total = prob_sum_function + prob_avg_function

    if aggregate_total <= 0.0:
        return expr

    use_aggregate = random.random() < min(aggregate_total, 1.0)
    if not use_aggregate:
        return expr

    agg_name = pick_aggregate_name(params)
    if agg_name is None:
        return expr

    wrapped_keys = [maybe_wrap_key_with_len(key, len_eligible_keys) for key in keys]

    return build_function_node(agg_name, wrapped_keys)


def build_arith_expr(
    keys: list[str],
    params: Params,
    len_eligible_keys: set[str] | None = None,
) -> Node:
    len_eligible_keys = len_eligible_keys or set()

    aggregate_total = float(getattr(params, "PROB_SUM_FUNCTION", 0.0)) + float(
        getattr(params, "PROB_AVG_FUNCTION", 0.0)
    )
    binary_total = (
        float(getattr(params, "PROB_SUM", 0.0))
        + float(getattr(params, "PROB_SUBSTRACT", 0.0))
        + float(getattr(params, "PROB_MULTIPLY", 0.0))
        + float(getattr(params, "PROB_DIVIDE", 0.0))
    )

    if (
        getattr(params, "AGGREGATE_FUNCTIONS", False)
        and len(keys) >= 2
        and aggregate_total > 0.0
        and binary_total <= 0.0
    ):
        agg_name = pick_aggregate_name(params)
        if agg_name is not None:
            wrapped_keys = [maybe_wrap_key_with_len(key, len_eligible_keys) for key in keys]
            return build_function_node(agg_name, wrapped_keys)

    expr = build_plain_arith_expr(keys, params, len_eligible_keys)
    return maybe_wrap_with_aggregate(expr, keys, params, len_eligible_keys)


def build_numeric_predicate(
    keys: list[str],
    params: Params,
    len_eligible_keys: set[str] | None = None,
) -> Node | None:
    if len(keys) < 2:
        return None

    len_eligible_keys = len_eligible_keys or set()

    split = random.randint(1, len(keys) - 1)
    left_keys = keys[:split]
    right_keys = keys[split:]

    if not left_keys or not right_keys:
        return None

    expr_left = build_arith_expr(left_keys, params, len_eligible_keys)
    expr_right = build_arith_expr(right_keys, params, len_eligible_keys)

    return Node(pick_cmp_op(params), expr_left, expr_right)


# -----------------------------
# String helpers
# -----------------------------


def build_string_predicate(keys: list[str], params: Params) -> Node | None:
    if len(keys) < 2:
        return None

    len_prob = float(getattr(params, "PROB_LEN_FUNCTION", 0.0))
    use_len = (
        getattr(params, "TYPE_LEVEL", False)
        and getattr(params, "STRING_CONSTRAINTS", False)
        and len_prob > 0.0
        and random.random() < len_prob
    )

    if use_len:
        wrapped_keys = [f"len({key})" for key in keys]
        return build_numeric_predicate(wrapped_keys, params)

    if len(keys) == 2:
        return Node(ASTOperation.EQUALS, Node(keys[0]), Node(keys[1]))

    eq_nodes: list[Node] = []
    index = 0

    while index + 1 < len(keys):
        eq_nodes.append(Node(ASTOperation.EQUALS, Node(keys[index]), Node(keys[index + 1])))
        index += 2

    if not eq_nodes:
        return None

    if len(eq_nodes) == 1:
        return eq_nodes[0]

    return build_left_deep_bool_ast(eq_nodes, params)


# -----------------------------
# Mixed constraint builder
# -----------------------------


def pick_predicate_kind(available_kinds: list[str], params: Params) -> str:
    weights = []

    for kind in available_kinds:
        if kind == "bool":
            weights.append(float(getattr(params, "CTC_DIST_BOOLEAN", 0.7)))
        elif kind == "num":
            weights.append(
                float(getattr(params, "CTC_DIST_INTEGER", 0.2)) + float(getattr(params, "CTC_DIST_REAL", 0.1))
            )
        elif kind == "string":
            weights.append(float(getattr(params, "CTC_DIST_STRING", 0.0)))
        else:
            weights.append(0.0)

    if sum(weights) <= 0.0:
        return random.choice(available_kinds)

    return random.choices(available_kinds, weights=weights, k=1)[0]


def build_mixed_constraint(
    bool_groups: dict[str, list[str]],
    num_groups: dict[str, list[str]],
    str_groups: dict[str, list[str]],
    numeric_len_groups: dict[str, list[str]],
    target_occ: int,
    params: Params,
    max_reps: int,
    max_features_param: int,
) -> Node | None:
    """
    Build a mixed constraint using boolean, numeric and string predicates.
    Example: F1 & F2 | (F3.Attr1 < len(F4)).
    """
    if target_occ < 1:
        return None

    for _ in range(50):
        remaining = target_occ
        feature_usage: dict[str, int] = {}
        selected_features: set[str] = set()
        predicate_nodes: list[Node] = []

        while remaining > 0:
            available_kinds: list[str] = []

            if bool_groups and remaining >= 1:
                available_kinds.append("bool")
            if (num_groups or numeric_len_groups) and remaining >= 2:
                available_kinds.append("num")
            if str_groups and remaining >= 2:
                available_kinds.append("string")

            if not available_kinds:
                break

            if remaining == 1 and "bool" in available_kinds:
                kind = "bool"
            else:
                kind = pick_predicate_kind(available_kinds, params)

            if kind == "bool":
                occ = random.randint(1, min(3, remaining))
                chosen = sample_keys_with_ecr(
                    bool_groups,
                    occ,
                    max_reps,
                    max_features_param,
                    feature_usage,
                    selected_features,
                )
                if not chosen:
                    break

                node = build_boolean_predicate(chosen, params)

            elif kind == "num":
                max_occ = min(4, remaining)
                if max_occ < 2:
                    break

                occ = random.randint(2, max_occ)

                merged_num_groups: dict[str, list[str]] = {}
                for source in (num_groups, numeric_len_groups):
                    for fid, values in source.items():
                        merged_num_groups.setdefault(fid, []).extend(values)

                chosen = sample_keys_with_ecr(
                    merged_num_groups,
                    occ,
                    max_reps,
                    max_features_param,
                    feature_usage,
                    selected_features,
                )
                if not chosen:
                    break

                len_eligible_keys = set()
                for values in numeric_len_groups.values():
                    len_eligible_keys.update(values)

                node = build_numeric_predicate(chosen, params, len_eligible_keys)

            else:
                max_occ = min(4, remaining)
                if max_occ < 2:
                    break

                occ = random.randint(2, max_occ)
                chosen = sample_keys_with_ecr(
                    str_groups,
                    occ,
                    max_reps,
                    max_features_param,
                    feature_usage,
                    selected_features,
                )
                if not chosen:
                    break

                node = build_string_predicate(chosen, params)

            if node is None:
                break

            predicate_nodes.append(node)
            remaining -= occ

        if remaining == 0 and predicate_nodes:
            if len(predicate_nodes) == 1:
                return predicate_nodes[0]

            return build_left_deep_bool_ast(predicate_nodes, params)

    return None
