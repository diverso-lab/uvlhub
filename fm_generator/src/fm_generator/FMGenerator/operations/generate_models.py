import sys
import random
import string
from flamapy.metamodels.fm_metamodel.models.feature_model import (
    FeatureModel,
    Feature,
    Relation,
    Constraint,
    Attribute,
    Domain,
    Range,
    Cardinality,
    FeatureType)
from flamapy.core.models.ast import AST, ASTOperation, Node
from fm_generator.FMGenerator.models.config import Params
from flamapy.core.discover import DiscoverMetamodels


def generate_random_attributes(
        params: Params,
        features: list[Feature]) -> None:
    num_attributes = random.randint(
        params.MIN_ATTRIBUTES,
        params.MAX_ATTRIBUTES)

    arithmetic_level_enabled = bool(getattr(params, "ARITHMETIC_LEVEL", False))
    min_vars_per_constraint = int(
        getattr(params, "MIN_VARS_PER_CONSTRAINT", 1))
    extra_constraint_repr = max(
        1, int(getattr(params, "EXTRA_CONSTRAINT_REPRESENTATIVENESS", 1)))

    # Si hay nivel aritmético, necesitamos suficientes attrs numéricos
    # repartidos en features distintas para que las constraints numéricas
    # sean realmente viables.
    required_numeric_attrs = 0
    numeric_weight = (
        float(getattr(params, "DIST_INTEGER", 0.0)) +
        float(getattr(params, "DIST_REAL", 0.0))
    )

    if arithmetic_level_enabled and numeric_weight > 0.0:
        required_numeric_attrs = (
            min_vars_per_constraint + extra_constraint_repr - 1
        ) // extra_constraint_repr
        required_numeric_attrs = min(
            required_numeric_attrs,
            num_attributes,
            len(features),
        )

    available_features_for_numeric = features[:]
    random.shuffle(available_features_for_numeric)

    def pick_random_attribute_type() -> str:
        attr_types = ["boolean", "integer", "real", "string"]
        weights = [
            float(getattr(params, "DIST_BOOLEAN", 0.0)),
            float(getattr(params, "DIST_INTEGER", 0.0)),
            float(getattr(params, "DIST_REAL", 0.0)),
            float(getattr(params, "DIST_STRING", 0.0)),
        ]

        if sum(weights) <= 0.0:
            return "boolean"

        return random.choices(attr_types, weights=weights, k=1)[0]

    for i in range(num_attributes):
        # Garantizamos attrs numéricos suficientes al principio
        if i < required_numeric_attrs:
            num_types = ["integer", "real"]
            num_weights = [
                float(getattr(params, "DIST_INTEGER", 0.0)),
                float(getattr(params, "DIST_REAL", 0.0)),
            ]
            attr_type = random.choices(num_types, weights=num_weights, k=1)[0]
            if available_features_for_numeric:
                feature = available_features_for_numeric.pop()
            else:
                feature = random.choice(features)
        else:
            feature = random.choice(features)
            attr_type = pick_random_attribute_type()

        attr_name = f"Attr{i}"

        if attr_type == 'boolean':
            domain = Domain(ranges=None, elements=[True, False])
            default = random.choice([True, False])

        elif attr_type == 'integer':
            min_val, max_val = random.randint(0, 50), random.randint(51, 100)
            domain = Domain(ranges=[Range(min_val, max_val)], elements=None)
            default = random.randint(min_val, max_val)

        elif attr_type == 'real':
            min_val, max_val = random.randint(0, 50), random.randint(51, 100)
            domain = Domain(ranges=[Range(min_val, max_val)], elements=None)
            default = round(random.uniform(min_val, max_val), 2)

        else:
            min_len = 1
            max_len = 50
            domain = Domain(ranges=[Range(min_len, max_len)], elements=None)
            length = random.randint(min_len, max_len)
            letters = string.ascii_letters + string.digits
            default = ''.join(random.choices(letters, k=length))

        attribute = Attribute(
            name=attr_name,
            domain=domain,
            default_value=default)
        setattr(attribute, "attribute_type", attr_type)
        attribute.set_parent(feature)
        feature.add_attribute(attribute)
        


def assign_manual_attributes(params: Params, features: list[Feature]) -> None:
    assert params.MIN_ATTRIBUTES is None and params.MAX_ATTRIBUTES is None, (
        "MIN_ATTRIBUTES and MAX_ATTRIBUTES must be None when using manual attributes."
    )
    attr_dicts = params.ATTRIBUTES_LIST

    for attr in attr_dicts:
        name = attr.get("name")
        type_ = attr.get("type", "").strip().lower()
        value = attr.get("value")
        min_value = attr.get("min_value")
        max_value = attr.get("max_value")
        # Por defecto 1.0 (seguro se añade)
        attach_prob = attr.get("attach_probability", 1.0)

        if type_ == "boolean":
            domain_values = value
            if not isinstance(domain_values, list):
                if domain_values in [True, False]:
                    domain_values = [domain_values]
                elif isinstance(domain_values, str):
                    v = domain_values.strip().lower()
                    if v == "true":
                        domain_values = [True]
                    elif v == "false":
                        domain_values = [False]
                    else:
                        domain_values = [True, False]
                else:
                    domain_values = [True, False]
            domain = Domain(ranges=None, elements=domain_values)

            def gen_default():
                return random.choice(domain_values)

        elif type_ == "integer":
            try:
                min_v = int(min_value)
            except Exception:
                min_v = 0
            try:
                max_v = int(max_value)
            except Exception:
                max_v = 10
            domain = Domain(ranges=[Range(min_v, max_v)], elements=None)

            def gen_default():
                return random.randint(min_v, max_v)

        elif type_ == "real":
            try:
                min_v = float(min_value)
            except Exception:
                min_v = 0.0
            try:
                max_v = float(max_value)
            except Exception:
                max_v = 1.0
            domain = Domain(ranges=[Range(min_v, max_v)], elements=None)

            def gen_default():
                return round(random.uniform(min_v, max_v), 3)

        elif type_ == "string":
            try:
                min_len = int(min_value)
            except Exception:
                min_len = 1
            try:
                max_len = int(max_value)
            except Exception:
                max_len = 10
            domain = Domain(ranges=[Range(min_len, max_len)], elements=None)

            def gen_default():
                length = random.randint(min_len, max_len)
                letters = string.ascii_letters + string.digits
                return ''.join(random.choices(letters, k=length))

        else:
            continue

        for feature in features:
            if random.random() < float(attach_prob):
                default = gen_default()
                attribute = Attribute(
                    name=name, domain=domain, default_value=default)
                setattr(attribute, "attribute_type", type_)
                attribute.set_parent(feature)
                feature.add_attribute(attribute)


def maybe_apply_feature_type(feature: Feature, params: Params) -> None:
    """Assign a type-level type to the feature according to independent probabilities.

    If no type is selected, the feature remains semantically Boolean without explicit type.
    If several probabilities succeed at once, one of the matched types is chosen randomly.
    """
    if not getattr(params, "TYPE_LEVEL", False):
        feature.feature_type = FeatureType.BOOLEAN
        setattr(feature, "is_type_level_typed", False)
        return

    candidates: list[FeatureType] = []

    if random.random() < float(getattr(params, "DIST_BOOLEAN", 0.0)):
        candidates.append(FeatureType.BOOLEAN)
    if random.random() < float(getattr(params, "DIST_INTEGER", 0.0)):
        candidates.append(FeatureType.INTEGER)
    if random.random() < float(getattr(params, "DIST_REAL", 0.0)):
        candidates.append(FeatureType.REAL)
    if random.random() < float(getattr(params, "DIST_STRING", 0.0)):
        candidates.append(FeatureType.STRING)

    if candidates:
        feature.feature_type = random.choice(candidates)
        setattr(feature, "is_type_level_typed", True)
    else:
        # Untyped feature: semantically equivalent to Boolean
        feature.feature_type = FeatureType.BOOLEAN
        setattr(feature, "is_type_level_typed", False)


def feature_constraint_bucket(feature: Feature, params: Params) -> str:
    """Return the constraint bucket where the feature must participate.

    Rules agreed with you:
    - untyped feature or Boolean feature -> bool
    - Integer / Real feature -> num
    - String feature -> string
    """
    if not getattr(params, "TYPE_LEVEL", False):
        return "bool"

    ftype = getattr(feature, "feature_type", FeatureType.BOOLEAN)

    if ftype in (FeatureType.INTEGER, FeatureType.REAL):
        return "num"
    if ftype == FeatureType.STRING:
        return "string"
    return "bool"


def constraints_must_be_boolean_only(params: Params) -> bool:
    return bool(getattr(params, "ENSURE_SATISFIABLE", False))


def select_relation_types(params: Params, total: int) -> list[str]:
    return random.choices(
        population=['mand', 'opt', 'alt', 'or', 'group'],
        weights=[
            params.DIST_MANDATORY,
            params.DIST_OPTIONAL,
            params.DIST_ALTERNATIVE,
            params.DIST_OR,
            params.DIST_GROUP_CARDINALITY
        ],
        k=total
    )


def determine_group_size(pool_size: int, params: Params) -> int:
    return random.randint(1, min(params.GROUP_CARDINALITY_MAX, pool_size))


def maybe_apply_feature_cardinality(feature: Feature, params: Params) -> None:
    if not getattr(params, "FEATURE_CARDINALITY", False):
        return

    prob = float(getattr(params, "PROB_FEATURE_CARDINALITY", 0.0))
    if random.random() >= prob:
        return

    fc_min_cfg = int(getattr(params, "MIN_FEATURE_CARDINALITY", 2))
    fc_max_cfg = int(getattr(params, "MAX_FEATURE_CARDINALITY", 5))

    if fc_min_cfg > fc_max_cfg:
        fc_min_cfg = fc_max_cfg

    fc_min = random.randint(fc_min_cfg, fc_max_cfg)
    fc_max = random.randint(fc_min, fc_max_cfg)

    feature.feature_cardinality = Cardinality(fc_min, fc_max)


def maybe_set_feature_cardinality(feature: Feature, params: Params) -> None:
    if not getattr(params, "FEATURE_CARDINALITY", False):
        return

    prob = float(getattr(params, "PROB_FEATURE_CARDINALITY", 0.0))
    if random.random() >= prob:
        return

    fc_min_cfg = int(getattr(params, "MIN_FEATURE_CARDINALITY", 2))
    fc_max_cfg = int(getattr(params, "MAX_FEATURE_CARDINALITY", 5))

    if fc_min_cfg > fc_max_cfg:
        fc_min_cfg = fc_max_cfg

    fc_min = random.randint(fc_min_cfg, fc_max_cfg)
    fc_max = random.randint(fc_min, fc_max_cfg)

    feature.cardinality_min = fc_min
    feature.cardinality_max = fc_max


def create_relation(
        parent: Feature,
        children: list[Feature],
        rel_kind: str,
        params: Params) -> list[Relation]:
    size = len(children)
    relations = []

    if rel_kind == 'mand':
        for child in children:
            rel = Relation(
                parent=parent,
                children=[child],
                card_min=1,
                card_max=1)
            relations.append(rel)

    elif rel_kind == 'opt':
        for child in children:
            rel = Relation(
                parent=parent,
                children=[child],
                card_min=0,
                card_max=1)
            relations.append(rel)

    elif rel_kind == 'alt':
        rel = Relation(
            parent=parent,
            children=children,
            card_min=1,
            card_max=1)
        relations.append(rel)

    elif rel_kind == 'or':
        rel = Relation(
            parent=parent,
            children=children,
            card_min=1,
            card_max=size)
        relations.append(rel)

    else:
        min_bound = max(params.GROUP_CARDINALITY_MIN, 1)
        max_bound = size
        if min_bound > max_bound:
            min_bound = max_bound
        card_min = random.randint(min_bound, max_bound)
        card_max = random.randint(card_min, max_bound)
        rel = Relation(
            parent=parent,
            children=children,
            card_min=card_min,
            card_max=card_max)
        relations.append(rel)

    return relations


def add_relations_to_level(
        parents: list[Feature],
        children: list[Feature],
        params: Params) -> None:
    total = len(children)
    rel_types = select_relation_types(params, total)
    random.shuffle(rel_types)
    pool = children[:]
    parent_idx = 0
    while pool:
        rel_kind = rel_types[parent_idx % len(rel_types)]
        parent = parents[parent_idx % len(parents)]
        parent_idx += 1
        size = determine_group_size(len(pool), params)
        group = [pool.pop() for _ in range(size)]
        relations = create_relation(parent, group, rel_kind, params)
        for rel in relations:
            parent.add_relation(rel)
            for child in rel.children:
                child.parent = parent
                maybe_apply_feature_cardinality(child, params)


def generate_hierarchy(params: Params) -> tuple[FeatureModel, list[Feature]]:
    root = Feature(name="F0")
    fm = FeatureModel(root=root)
    numFeats = random.randint(params.MIN_FEATURES, params.MAX_FEATURES)
    names = [f"F{i + 1}" for i in range(numFeats)]
    features = [Feature(name=n) for n in names]
    for feature in features:
        maybe_apply_feature_type(feature, params)
    levels = {0: [root]}
    idx = 0
    total = 0
    max_depth = params.MAX_TREE_DEPTH

    for depth in range(1, max_depth + 1):
        remaining = numFeats - total
        if remaining <= 0:
            break
        parents = levels.get(depth - 1, [])
        if not parents:
            break
        levels_left = max_depth - depth + 1
        level_count = max(1, remaining // levels_left)
        if depth == max_depth:
            level_count = remaining
        level_feats = features[idx: idx + level_count]
        levels[depth] = level_feats
        idx += level_count
        total += level_count
        add_relations_to_level(parents, level_feats, params)

    connected = {f.name for f in fm.get_features()}
    return fm, [f for f in features if f.name in connected]


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

    def choose_target_occurrences(groups: dict[str, list[str]]) -> int | None:
        if not groups:
            return None

        max_by_ecr = max_occurrences_possible(groups)
        effective_max = min(max_vars, max_by_ecr)
        effective_min = min_vars

        if effective_max < effective_min:
            return None

        return random.randint(effective_min, effective_max)

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


def build_uvl_includes(params: Params) -> list[str]:
    includes: list[str] = []

    if getattr(params, "GROUP_CARDINALITY", False):
        includes.append("Boolean.group-cardinality")

    arithmetic_feature_cardinality = bool(
        getattr(params, "FEATURE_CARDINALITY", False))
    arithmetic_aggregate_functions = bool(
        getattr(params, "AGGREGATE_FUNCTIONS", False))

    if arithmetic_feature_cardinality and arithmetic_aggregate_functions:
        includes.append("Arithmetic.*")
    else:
        if arithmetic_aggregate_functions:
            includes.append("Arithmetic.aggregate-function")
        if arithmetic_feature_cardinality:
            includes.append("Arithmetic.feature-cardinality")

    if getattr(
        params,
        "TYPE_LEVEL",
        False) and getattr(
        params,
        "STRING_CONSTRAINTS",
            False):
        includes.append("Type.string-constraints")

    return includes


SATISFIABILITY_MAX_ATTEMPTS = 30
SAT_SEED_STRIDE = 100000
_SAT_BACKEND_WARNING_EMITTED = False


def is_model_satisfiable(feature_model: FeatureModel) -> bool:
    """Best-effort satisfiability check.

    In CPython we try PySAT. In Pyodide, python-sat/pysat is usually not
    available, so we avoid returning False just because the SAT backend cannot
    be loaded. Returning True in that case means: "generation may continue,
    but satisfiability could not be certified in this runtime".
    """
    global _SAT_BACKEND_WARNING_EMITTED

    try:
        dm = DiscoverMetamodels()
        sat_model = dm.use_transformation_m2m(feature_model, "pysat")
        operation = dm.get_operation(sat_model, "PySATSatisfiable")
        operation.execute(sat_model)
        return bool(operation.get_result())

    except ModuleNotFoundError as exc:
        missing = getattr(exc, "name", "")

        if missing in {"pysat", "pycryptosat"}:
            if not _SAT_BACKEND_WARNING_EMITTED:
                print(
                    "[SAT WARNING] PySAT backend is not available in this runtime; "
                    "continuing without SAT certification."
                )
                _SAT_BACKEND_WARNING_EMITTED = True
            return True

        raise

    except Exception as exc:
        msg = str(exc)

        if "No module named 'pysat'" in msg or "No module named pysat" in msg:
            if not _SAT_BACKEND_WARNING_EMITTED:
                print(
                    "[SAT WARNING] PySAT backend is not available in this runtime; "
                    "continuing without SAT certification."
                )
                _SAT_BACKEND_WARNING_EMITTED = True
            return True

        print(f"[SAT ERROR] PySAT satisfiability check failed: {exc}")
        return False


def generate_single_model(
        params: Params,
        index: int,
        attempt: int = 0) -> FeatureModel:
    seed_value = params.SEED + index + (attempt * SAT_SEED_STRIDE)
    random.seed(seed_value)

    fm, feats = generate_hierarchy(params)
    if params.RANDOM_ATTRIBUTES:
        generate_random_attributes(params, feats)
    else:
        assign_manual_attributes(params, feats)
    add_constraints(fm, feats, params)

    setattr(fm, "uvl_includes", build_uvl_includes(params))

    return fm
