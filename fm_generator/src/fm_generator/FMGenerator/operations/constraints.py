import random

from flamapy.metamodels.fm_metamodel.models.feature_model import (
    FeatureModel,
    Feature,
    Attribute,
    Constraint,
)

from flamapy.core.models.ast import AST, ASTOperation, Node

from fm_generator.FMGenerator.models.config import Params
from fm_generator.FMGenerator.operations.hierarchy import feature_constraint_bucket


def constraints_must_be_boolean_only(params: Params) -> bool:
    return bool(getattr(params, "ENSURE_SATISFIABLE", False))


def add_constraints(
        fm: FeatureModel,
        features: list[Feature],
        params: Params) -> None:
    RANDOM_ATTR_CONSTRAINT_PROB = 0.8
    boolean_only_constraints = constraints_must_be_boolean_only(params)
    attrs_bool: list[tuple[Feature, Attribute, float]] = []
    attrs_num: list[tuple[Feature, Attribute, float]] = []
    attrs_str: list[tuple[Feature, Attribute, float]] = []

    for feat in features:
        for attr in getattr(feat, "attributes", []):
            attr_type = None
            use_in_constraints = False
            constraint_probability = None

            # -------------------------
            # Manual attributes
            # -------------------------
            if hasattr(params, "ATTRIBUTES_LIST"):
                for attr_dict in params.ATTRIBUTES_LIST:
                    if attr_dict.get(
                            "name") == attr.name and feat.name and attr.name:
                        attr_type = (attr_dict.get("type", "") or "").lower()
                        use_in_constraints = attr_dict.get(
                            "use_in_constraints", False)
                        constraint_probability = float(
                            attr_dict.get("attach_probability", 1.0))
                        break

            # -------------------------
            # Random attributes
            # -------------------------
            is_manual_attribute = False

            if attr_type is None:
                raw_attr_type = getattr(attr, "attribute_type", None)

                if raw_attr_type is not None:
                    attr_type = getattr(
                        raw_attr_type, "value", str(raw_attr_type)).lower()
                else:
                    domain = getattr(attr, "domain", None)
                    elements = getattr(domain, "elements", None) or []
                    ranges = getattr(domain, "ranges", None) or []

                    if elements:
                        attr_type = "boolean"
                    elif ranges:
                        r = ranges[0]
                        range_min = getattr(r, "min_value", None)
                        range_max = getattr(r, "max_value", None)

                        if isinstance(
                                range_min,
                                int) and isinstance(
                                range_max,
                                int):
                            attr_type = "integer"
                        elif isinstance(range_min, float) or isinstance(range_max, float):
                            attr_type = "real"
                        else:
                            attr_type = "string"
                    else:
                        attr_type = "string"

                use_in_constraints = True
                constraint_probability = RANDOM_ATTR_CONSTRAINT_PROB
            else:
                is_manual_attribute = True

            if boolean_only_constraints:
                continue

            if not use_in_constraints:
                continue

            constraint_probability = max(
                0.0, min(float(constraint_probability), 1.0))
            attr_tuple = (feat, attr, constraint_probability)

            if attr_type == "boolean":
                attrs_bool.append(attr_tuple)

            elif attr_type in ("integer", "real"):
                if getattr(params, "ARITHMETIC_LEVEL", False):
                    attrs_num.append(attr_tuple)

            elif attr_type == "string":
                if is_manual_attribute:
                    # Los atributos manuales string pueden usarse en constraints
                    # aunque STRING_CONSTRAINTS no esté activado.
                    attrs_str.append(attr_tuple)
                else:
                    # Los string aleatorios siguen dependiendo del minor level.
                    if (
                        getattr(params, "TYPE_LEVEL", False)
                        and getattr(params, "STRING_CONSTRAINTS", False)
                    ):
                        attrs_str.append(attr_tuple)

    if boolean_only_constraints:
        feats_bool = [
            f for f in features if feature_constraint_bucket(
                f, params) == "bool"]
        feats_num = []
        feats_str = []
    else:
        feats_bool = [
            f for f in features if feature_constraint_bucket(
                f, params) == "bool"]
        feats_num = [
            f for f in features if feature_constraint_bucket(
                f, params) == "num"]
        feats_str = [
            f for f in features if feature_constraint_bucket(
                f, params) == "string"]

    def filter_attrs_for_constraint(
        attr_pool: list[tuple[Feature, Attribute, float]]
    ) -> list[tuple[Feature, Attribute]]:
        filtered: list[tuple[Feature, Attribute]] = []
        for feat, attr, prob in attr_pool:
            if random.random() < prob:
                filtered.append((feat, attr))
        return filtered

    def ensure_non_empty_filtered_pool(
        filtered_pool: list[tuple[Feature, Attribute]],
        original_pool: list[tuple[Feature, Attribute, float]]
    ) -> list[tuple[Feature, Attribute]]:
        if filtered_pool or not original_pool:
            return filtered_pool

        # Si no ha entrado ninguno por probabilidad, damos una oportunidad
        # a que entre uno al menos, escogido ponderadamente por su
        # attach_probability.
        weights = [max(0.0, prob) for _, _, prob in original_pool]
        if sum(weights) <= 0.0:
            return []

        feat, attr, _ = random.choices(original_pool, weights=weights, k=1)[0]
        return [(feat, attr)]

    def filter_len_groups_for_numeric_use(
        len_groups: dict[str, list[str]],
        len_prob: float,
    ) -> dict[str, list[str]]:
        filtered: dict[str, list[str]] = {}

        if len_prob <= 0.0:
            return filtered

        for fid, values in len_groups.items():
            selected_values = [
                value for value in values if random.random() < len_prob]
            if selected_values:
                filtered[fid] = selected_values

        return filtered

    # -----------------------------
    # Params y caps
    # -----------------------------
    min_vars = int(getattr(params, "MIN_VARS_PER_CONSTRAINT", 1))
    max_vars = int(getattr(params, "MAX_VARS_PER_CONSTRAINT", 2))

    min_vars = max(1, min_vars)
    max_vars = max(1, max_vars)

    if min_vars > max_vars:
        min_vars = max_vars

    # ECR: ahora es <= max_vars (clamp), mínimo 1
    max_reps = int(getattr(params, "EXTRA_CONSTRAINT_REPRESENTATIVENESS", 1))
    max_reps = max(1, max_reps)
    max_reps = min(max_reps, max_vars)

    # MAX_FEATURES del step2: lo usamos como máximo de FEATURES DISTINTAS por
    # constraint
    max_features_param = int(getattr(params, "MAX_FEATURES", 10))
    max_features_param = max(1, max_features_param)

    # -----------------------------
    # Helpers de operaciones
    # -----------------------------
    def pick_bool_op() -> ASTOperation:
        ops = [
            ASTOperation.AND,
            ASTOperation.OR,
            ASTOperation.IMPLIES,
            ASTOperation.EQUIVALENCE]
        weights = [
            float(getattr(params, "PROB_AND", 0.7)),
            float(getattr(params, "PROB_OR_CT", 0.1)),
            float(getattr(params, "PROB_IMPLICATION", 0.1)),
            float(getattr(params, "PROB_EQUIVALENCE", 0.1)),
        ]
        return random.choices(ops, weights=weights, k=1)[0]

    def maybe_not(node: Node) -> Node:
        if random.random() < float(getattr(params, "PROB_NOT", 0.0)):
            return Node(ASTOperation.NOT, node)
        return node

    def build_left_deep_bool_ast(nodes: list[Node]) -> Node:
        """(((n1 op n2) op n3) op n4) ..."""
        assert len(nodes) >= 2
        cur = Node(pick_bool_op(), nodes[0], nodes[1])
        for n in nodes[2:]:
            cur = Node(pick_bool_op(), cur, n)
        return cur

    # -----------------------------
    # ECR es por FEATURE (no por key)
    # key: "F12" o "F12.attr"
    # feature_id = "F12"
    # -----------------------------
    def feature_id_from_key(key: str) -> str:
        return key.split(".", 1)[0]

    def group_keys_by_feature(keys: list[str]) -> dict[str, list[str]]:
        groups: dict[str, list[str]] = {}
        for k in keys:
            fid = feature_id_from_key(k)
            groups.setdefault(fid, []).append(k)
        return groups

    def distinct_feature_cap(groups: dict[str, list[str]]) -> int:
        return min(len(groups), max_features_param)

    def max_occurrences_possible(groups: dict[str, list[str]]) -> int:
        """
        Con ECR, si eliges X features distintas, máximo apariciones = X * ECR.
        Pero X está limitado por MAX_FEATURES (step2) y por cuántas features haya.
        """
        df_cap = distinct_feature_cap(groups)
        return df_cap * max_reps

    def sample_keys_with_ecr(
        groups: dict[str, list[str]],
        target_occ: int,
        feature_usage: dict[str, int] | None = None,
        selected_features: set[str] | None = None,
    ) -> list[str] | None:
        """
        Devuelve una lista de keys de longitud target_occ.
        Permite repetir keys, pero restringe por feature_id a max_reps apariciones.
        Además limita el número de features distintas usadas por MAX_FEATURES.
        """
        if target_occ < 1:
            return None

        feature_usage = {} if feature_usage is None else feature_usage
        selected_features = set() if selected_features is None else selected_features

        out: list[str] = []

        for _ in range(target_occ):
            allowed_fids = [
                fid for fid in groups if feature_usage.get(
                    fid, 0) < max_reps and (
                    fid in selected_features or len(selected_features) < max_features_param)]

            if not allowed_fids:
                return None

            fid = random.choice(allowed_fids)
            out.append(random.choice(groups[fid]))
            feature_usage[fid] = feature_usage.get(fid, 0) + 1
            selected_features.add(fid)

        random.shuffle(out)
        return out

    # -----------------------------
    # Numeric helpers
    # -----------------------------
    def pick_binary_arith_op() -> ASTOperation:
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

    def pick_cmp_op() -> ASTOperation:
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

    def pick_aggregate_name() -> str | None:
        if not getattr(params, "AGGREGATE_FUNCTIONS", False):
            return None

        prob_sum_function = float(getattr(params, "PROB_SUM_FUNCTION", 0.0))
        prob_avg_function = float(getattr(params, "PROB_AVG_FUNCTION", 0.0))

        total = prob_sum_function + prob_avg_function
        if total <= 0.0:
            return None

        names = ["sum", "avg"]
        weights = [prob_sum_function, prob_avg_function]
        return random.choices(names, weights=weights, k=1)[0]

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
            len_eligible_keys: set[str] | None = None) -> Node:
        len_eligible_keys = len_eligible_keys or set()

        first_key = maybe_wrap_key_with_len(keys[0], len_eligible_keys)
        cur = build_function_style_node(first_key)

        for k in keys[1:]:
            wrapped_key = maybe_wrap_key_with_len(k, len_eligible_keys)
            cur = Node(
                pick_binary_arith_op(),
                cur,
                build_function_style_node(wrapped_key))

        return cur

    def maybe_wrap_with_aggregate(
        expr: Node,
        keys: list[str],
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

        agg_name = pick_aggregate_name()
        if agg_name is None:
            return expr

        wrapped_keys = [
            maybe_wrap_key_with_len(k, len_eligible_keys)
            for k in keys
        ]
        return build_function_node(agg_name, wrapped_keys)

    def build_arith_expr(
            keys: list[str],
            len_eligible_keys: set[str] | None = None) -> Node:
        len_eligible_keys = len_eligible_keys or set()

        aggregate_total = (
            float(getattr(params, "PROB_SUM_FUNCTION", 0.0)) +
            float(getattr(params, "PROB_AVG_FUNCTION", 0.0))
        )

        binary_total = (
            float(getattr(params, "PROB_SUM", 0.0)) +
            float(getattr(params, "PROB_SUBSTRACT", 0.0)) +
            float(getattr(params, "PROB_MULTIPLY", 0.0)) +
            float(getattr(params, "PROB_DIVIDE", 0.0))
        )

        if (
            getattr(params, "AGGREGATE_FUNCTIONS", False)
            and len(keys) >= 2
            and aggregate_total > 0.0
            and binary_total <= 0.0
        ):
            agg_name = pick_aggregate_name()
            if agg_name is not None:
                wrapped_keys = [
                    maybe_wrap_key_with_len(k, len_eligible_keys)
                    for k in keys
                ]
                return build_function_node(agg_name, wrapped_keys)

        expr = build_plain_arith_expr(keys, len_eligible_keys)
        expr = maybe_wrap_with_aggregate(expr, keys, len_eligible_keys)
        return expr

    def build_boolean_predicate(keys: list[str]) -> Node | None:
        if not keys:
            return None

        literals = [maybe_not(Node(k)) for k in keys]

        if len(literals) == 1:
            return literals[0]

        return build_left_deep_bool_ast(literals)

    def build_numeric_predicate(
        keys: list[str],
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

        expr_left = build_arith_expr(left_keys, len_eligible_keys)
        expr_right = build_arith_expr(right_keys, len_eligible_keys)
        return Node(pick_cmp_op(), expr_left, expr_right)

    def build_string_predicate(keys: list[str]) -> Node | None:
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
            wrapped_keys = [f"len({k})" for k in keys]
            return build_numeric_predicate(wrapped_keys)

        if len(keys) == 2:
            return Node(ASTOperation.EQUALS, Node(keys[0]), Node(keys[1]))

        eq_nodes: list[Node] = []
        i = 0
        while i + 1 < len(keys):
            eq_nodes.append(
                Node(ASTOperation.EQUALS, Node(keys[i]), Node(keys[i + 1]))
            )
            i += 2

        if not eq_nodes:
            return None
        if len(eq_nodes) == 1:
            return eq_nodes[0]

        return build_left_deep_bool_ast(eq_nodes)

    def pick_predicate_kind(available_kinds: list[str]) -> str:
        weights = []
        for kind in available_kinds:
            if kind == "bool":
                weights.append(float(getattr(params, "CTC_DIST_BOOLEAN", 0.7)))
            elif kind == "num":
                weights.append(
                    float(getattr(params, "CTC_DIST_INTEGER", 0.2)) +
                    float(getattr(params, "CTC_DIST_REAL", 0.1))
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
    ) -> Node | None:
        """
        Construye una constraint mezclando predicados booleanos, numéricos y string
        dentro de una misma fórmula lógica.
        Ejemplo válido: F1 & F2 | (F3.Attr1 < len(F4))
        """
        if target_occ < 1:
            return None

        # varios intentos para evitar callejones sin salida
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

                # Si solo queda 1 variable, obligatoriamente booleano
                if remaining == 1 and "bool" in available_kinds:
                    kind = "bool"
                else:
                    kind = pick_predicate_kind(available_kinds)

                if kind == "bool":
                    # Para no generar monstruos, un predicado booleano consume
                    # entre 1 y 3 vars
                    occ = random.randint(1, min(3, remaining))
                    chosen = sample_keys_with_ecr(
                        bool_groups, occ, feature_usage, selected_features)
                    if not chosen:
                        break
                    node = build_boolean_predicate(chosen)

                elif kind == "num":
                    max_occ = min(4, remaining)
                    if max_occ < 2:
                        break
                    occ = random.randint(2, max_occ)

                    merged_num_groups: dict[str, list[str]] = {}
                    for source in (num_groups, numeric_len_groups):
                        for fid, values in source.items():
                            merged_num_groups.setdefault(
                                fid, []).extend(values)

                    chosen = sample_keys_with_ecr(
                        merged_num_groups,
                        occ,
                        feature_usage,
                        selected_features
                    )
                    if not chosen:
                        break

                    len_eligible_keys = set()
                    for values in numeric_len_groups.values():
                        len_eligible_keys.update(values)

                    node = build_numeric_predicate(chosen, len_eligible_keys)

                else:  # string
                    # Igualdades de string: mínimo 2
                    max_occ = min(4, remaining)
                    if max_occ < 2:
                        break
                    occ = random.randint(2, max_occ)
                    chosen = sample_keys_with_ecr(
                        str_groups, occ, feature_usage, selected_features)
                    if not chosen:
                        break
                    node = build_string_predicate(chosen)

                if node is None:
                    break

                predicate_nodes.append(node)
                remaining -= occ

            if remaining == 0 and predicate_nodes:
                if len(predicate_nodes) == 1:
                    return predicate_nodes[0]
                return build_left_deep_bool_ast(predicate_nodes)

        return None

    # -----------------------------
    # Generación de constraints
    # -----------------------------
    total_ctcs = random.randint(params.MIN_CONSTRAINTS, params.MAX_CONSTRAINTS)

    for i in range(total_ctcs):
        filtered_bool_attrs = ensure_non_empty_filtered_pool(
            filter_attrs_for_constraint(attrs_bool),
            attrs_bool
        )
        filtered_num_attrs = ensure_non_empty_filtered_pool(
            filter_attrs_for_constraint(attrs_num),
            attrs_num
        )
        filtered_str_attrs = ensure_non_empty_filtered_pool(
            filter_attrs_for_constraint(attrs_str),
            attrs_str
        )

        bool_pool = [f.name for f in feats_bool] + \
            [f"{f.name}.{a.name}" for f, a in filtered_bool_attrs]
        num_pool = [f.name for f in feats_num] + \
            [f"{f.name}.{a.name}" for f, a in filtered_num_attrs]
        str_pool = [f.name for f in feats_str] + \
            [f"{f.name}.{a.name}" for f, a in filtered_str_attrs]

        bool_groups = group_keys_by_feature(list(set(bool_pool)))
        num_groups = group_keys_by_feature(list(set(num_pool)))
        str_groups = group_keys_by_feature(list(set(str_pool)))

        len_prob = float(getattr(params, "PROB_LEN_FUNCTION", 0.0))

        # Candidatos string que pueden transformarse a len(...)
        len_pool = []
        if (
            not boolean_only_constraints
            and getattr(params, "TYPE_LEVEL", False)
            and getattr(params, "STRING_CONSTRAINTS", False)
        ):
            len_pool.extend([f.name for f in feats_str])
            len_pool.extend(
                [f"{f.name}.{a.name}" for f, a in filtered_str_attrs])

        len_groups = group_keys_by_feature(list(set(len_pool)))
        numeric_len_groups = filter_len_groups_for_numeric_use(
            len_groups, len_prob)

        # capacidad aproximada total: suma de capacidades por bucket
        total_capacity = 0
        if bool_groups:
            total_capacity += max_occurrences_possible(bool_groups)
        if num_groups:
            total_capacity += max_occurrences_possible(num_groups)
        if str_groups:
            total_capacity += max_occurrences_possible(str_groups)
        if numeric_len_groups:
            total_capacity += max_occurrences_possible(numeric_len_groups)

        effective_max = min(max_vars, total_capacity)
        effective_min = min_vars

        if effective_max < effective_min:
            continue

        target_occ = random.randint(effective_min, effective_max)

        if boolean_only_constraints:
            if not bool_groups:
                continue

            bool_capacity = max_occurrences_possible(bool_groups)
            effective_max = min(max_vars, bool_capacity)
            effective_min = min_vars

            if effective_max < effective_min:
                continue

            target_occ = random.randint(effective_min, effective_max)
            chosen = sample_keys_with_ecr(bool_groups, target_occ)

            if not chosen:
                continue

            root = build_boolean_predicate(chosen)
        else:
            root = build_mixed_constraint(
                bool_groups,
                num_groups,
                str_groups,
                numeric_len_groups,
                target_occ
            )
        if root is None:
            continue

        fm.ctcs.append(Constraint(name=f"ctc{i}", ast=AST(root)))
