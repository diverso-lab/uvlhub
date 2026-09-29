import random
import string

from flamapy.core.operations import Operation
from flamapy.core.models.ast import AST, ASTOperation, Node
from flamapy.metamodels.fm_metamodel.models.feature_model import (
    Attribute,
    Cardinality,
    Constraint,
    Domain,
    Feature,
    FeatureModel,
    FeatureType,
    Range,
    Relation,
)

from flamapy.metamodels.fm_generator.models import FmgeneratorModel

SAT_SEED_STRIDE = 100000
RANDOM_ATTR_CONSTRAINT_PROB = 0.8

__all__ = [
    "GenerateFeatureModel",
    "SAT_SEED_STRIDE",
]


class GenerateFeatureModel(Operation):
    """Operation responsible for generating FeatureModel instances from FmgeneratorModel."""

    def __init__(self) -> None:
        self.model: FmgeneratorModel | None = None
        self.result: FeatureModel | None = None

    def execute(
        self,
        model: FmgeneratorModel,
        index: int = 0,
        attempt: int = 0,
    ) -> Operation:

        self.model = model

        self.model.validate()
        self._seed_generation(index, attempt)

        fm, features = self._generate_hierarchy()
        self._assign_attributes(features)
        self._add_constraints(fm, features)

        setattr(fm, "uvl_includes", self._build_uvl_includes())

        self.result = fm
        return self

    def get_result(self) -> FeatureModel | None:
        return self.result

    def _seed_generation(self, index: int, attempt: int) -> None:
        seed_value = self.model.seed + index + (attempt * SAT_SEED_STRIDE)
        random.seed(seed_value)

    def _build_uvl_includes(self) -> list[str]:
        includes: list[str] = []
        if self.model.ensure_satisfiable:
            return []

        if self.model.levels.group_cardinality:
            includes.append("Boolean.group-cardinality")

        feature_cardinality = self.model.levels.feature_cardinality
        aggregate_functions = self.model.levels.aggregate_functions

        if feature_cardinality and aggregate_functions:
            includes.append("Arithmetic.*")
        else:
            if aggregate_functions:
                includes.append("Arithmetic.aggregate-function")
            if feature_cardinality:
                includes.append("Arithmetic.feature-cardinality")

        if self.model.levels.type_level and self.model.levels.string_constraints:
            includes.append("Type.string-constraints")

        return includes

    # -------------------------------------------------------------------------
    # Hierarchy generation
    # -------------------------------------------------------------------------

    def _maybe_apply_feature_type(self, feature: Feature) -> None:
        if self.model.ensure_satisfiable:
            feature.feature_type = FeatureType.BOOLEAN
            setattr(feature, "is_type_level_typed", False)
            return
        if not self.model.levels.type_level:
            feature.feature_type = FeatureType.BOOLEAN
            setattr(feature, "is_type_level_typed", False)
            return

        candidates: list[FeatureType] = []

        if random.random() < self.model.features.dist_boolean:
            candidates.append(FeatureType.BOOLEAN)
        if random.random() < self.model.features.dist_integer:
            candidates.append(FeatureType.INTEGER)
        if random.random() < self.model.features.dist_real:
            candidates.append(FeatureType.REAL)
        if random.random() < self.model.features.dist_string:
            candidates.append(FeatureType.STRING)

        if candidates:
            feature.feature_type = random.choice(candidates)
            setattr(feature, "is_type_level_typed", True)
        else:
            feature.feature_type = FeatureType.BOOLEAN
            setattr(feature, "is_type_level_typed", False)

    def _feature_constraint_bucket(self, feature: Feature) -> str:
        if not self.model.levels.type_level:
            return "bool"

        feature_type = getattr(feature, "feature_type", FeatureType.BOOLEAN)

        if feature_type in (FeatureType.INTEGER, FeatureType.REAL):
            return "num"
        if feature_type == FeatureType.STRING:
            return "string"
        return "bool"

    def _select_relation_types(self, total: int) -> list[str]:
        population = ["mand", "opt", "alt", "or", "group"]
        weights = [
            self.model.hierarchy.dist_mandatory,
            self.model.hierarchy.dist_optional,
            self.model.hierarchy.dist_alternative,
            self.model.hierarchy.dist_or,
            self.model.hierarchy.dist_group_cardinality,
        ]

        if self.model.ensure_satisfiable:
            population = population[:-1]
            weights = weights[:-1]

            # If all configured weight was assigned to group cardinality,
            # use mandatory relations for this Boolean-only generation.
            if sum(weights) <= 0:
                weights = [1.0, 0.0, 0.0, 0.0]

        return random.choices(population, weights=weights, k=total)

    def _determine_group_size(self, pool_size: int) -> int:
        if self.model.ensure_satisfiable:
            # Ordinary alternative/OR groups do not use the configured
            # group-cardinality limit.
            return random.randint(1, min(6, pool_size))

        return random.randint(
            1,
            min(self.model.hierarchy.group_cardinality_max, pool_size),
        )

    def _maybe_apply_feature_cardinality(self, feature: Feature) -> None:
        if self.model.ensure_satisfiable or not self.model.levels.feature_cardinality:
            return

        if random.random() >= self.model.features.prob_feature_cardinality:
            return

        min_cfg = self.model.features.min_feature_cardinality
        max_cfg = self.model.features.max_feature_cardinality

        if min_cfg > max_cfg:
            min_cfg = max_cfg

        card_min = random.randint(min_cfg, max_cfg)
        card_max = random.randint(card_min, max_cfg)

        feature.feature_cardinality = Cardinality(card_min, card_max)

    def _create_relation(
        self,
        parent: Feature,
        children: list[Feature],
        relation_kind: str,
    ) -> list[Relation]:
        size = len(children)
        relations: list[Relation] = []

        if relation_kind == "mand":
            for child in children:
                relations.append(Relation(parent=parent, children=[child], card_min=1, card_max=1))

        elif relation_kind == "opt":
            for child in children:
                relations.append(Relation(parent=parent, children=[child], card_min=0, card_max=1))

        elif relation_kind == "alt":
            relations.append(Relation(parent=parent, children=children, card_min=1, card_max=1))

        elif relation_kind == "or":
            relations.append(Relation(parent=parent, children=children, card_min=1, card_max=size))

        else:
            min_bound = max(self.model.hierarchy.group_cardinality_min, 1)
            max_bound = size

            if min_bound > max_bound:
                min_bound = max_bound

            card_min = random.randint(min_bound, max_bound)
            card_max = random.randint(card_min, max_bound)

            relations.append(
                Relation(
                    parent=parent,
                    children=children,
                    card_min=card_min,
                    card_max=card_max,
                )
            )

        return relations

    def _add_relations_to_level(
        self,
        parents: list[Feature],
        children: list[Feature],
    ) -> None:
        total = len(children)
        relation_types = self._select_relation_types(total)
        random.shuffle(relation_types)

        pool = children[:]
        parent_index = 0

        while pool:
            relation_kind = relation_types[parent_index % len(relation_types)]
            parent = parents[parent_index % len(parents)]
            parent_index += 1

            size = self._determine_group_size(len(pool))
            group = [pool.pop() for _ in range(size)]

            relations = self._create_relation(parent, group, relation_kind)

            for relation in relations:
                parent.add_relation(relation)

                for child in relation.children:
                    child.parent = parent
                    self._maybe_apply_feature_cardinality(child)

    def _generate_hierarchy(self) -> tuple[FeatureModel, list[Feature]]:
        root = Feature(name="F0")
        if self.model.ensure_satisfiable:
            self._maybe_apply_feature_type(root)
        fm = FeatureModel(root=root)

        num_features = random.randint(
            self.model.features.min_features,
            self.model.features.max_features,
        )

        names = [f"F{i + 1}" for i in range(num_features)]
        features = [Feature(name=name) for name in names]

        for feature in features:
            self._maybe_apply_feature_type(feature)

        levels: dict[int, list[Feature]] = {0: [root]}
        index = 0
        total = 0
        max_depth = self.model.hierarchy.max_tree_depth

        for depth in range(1, max_depth + 1):
            remaining = num_features - total

            if remaining <= 0:
                break

            parents = levels.get(depth - 1, [])

            if not parents:
                break

            levels_left = max_depth - depth + 1
            level_count = max(1, remaining // levels_left)

            if depth == max_depth:
                level_count = remaining

            level_features = features[index : index + level_count]
            levels[depth] = level_features

            index += level_count
            total += level_count

            self._add_relations_to_level(parents, level_features)

        connected = {feature.name for feature in fm.get_features()}
        return fm, [feature for feature in features if feature.name in connected]

    # -------------------------------------------------------------------------
    # Attribute generation
    # -------------------------------------------------------------------------

    def _assign_attributes(self, features: list[Feature]) -> None:
        if self.model.ensure_satisfiable:
            return
        if self.model.attributes.random_attributes:
            self._generate_random_attributes(features)
        else:
            self._assign_manual_attributes(features)

    def _pick_random_attribute_type(self) -> str:
        attribute_types = ["boolean", "integer", "real", "string"]
        weights = [
            self.model.attributes.dist_boolean_atr,
            self.model.attributes.dist_integer_atr,
            self.model.attributes.dist_real_atr,
            self.model.attributes.dist_string_atr,
        ]

        if sum(weights) <= 0.0:
            return "boolean"

        return random.choices(attribute_types, weights=weights, k=1)[0]

    def _generate_random_attributes(self, features: list[Feature]) -> None:
        if self.model.attributes.min_attributes is None:
            raise ValueError("[ERROR] min_attributes cannot be None in random mode.")

        if self.model.attributes.max_attributes is None:
            raise ValueError("[ERROR] max_attributes cannot be None in random mode.")

        num_attributes = random.randint(
            self.model.attributes.min_attributes,
            self.model.attributes.max_attributes,
        )

        required_numeric_attributes = 0
        numeric_weight = self.model.attributes.dist_integer_atr + self.model.attributes.dist_real_atr

        if self.model.levels.arithmetic_level and numeric_weight > 0.0:
            required_numeric_attributes = (
                self.model.constraints.min_vars_per_constraint
                + self.model.constraints.extra_constraint_representativeness
                - 1
            ) // self.model.constraints.extra_constraint_representativeness

            required_numeric_attributes = min(
                required_numeric_attributes,
                num_attributes,
                len(features),
            )

        available_features_for_numeric = features[:]
        random.shuffle(available_features_for_numeric)

        for index in range(num_attributes):
            if index < required_numeric_attributes:
                numeric_types = ["integer", "real"]
                numeric_weights = [
                    self.model.attributes.dist_integer_atr,
                    self.model.attributes.dist_real_atr,
                ]

                attribute_type = random.choices(
                    numeric_types,
                    weights=numeric_weights,
                    k=1,
                )[0]

                if available_features_for_numeric:
                    feature = available_features_for_numeric.pop()
                else:
                    feature = random.choice(features)
            else:
                feature = random.choice(features)
                attribute_type = self._pick_random_attribute_type()

            attribute = self._create_random_attribute(index, attribute_type)
            attribute.set_parent(feature)
            feature.add_attribute(attribute)

    def _create_random_attribute(self, index: int, attribute_type: str) -> Attribute:
        attribute_name = f"Attr{index}"

        if attribute_type == "boolean":
            domain = Domain(ranges=None, elements=[True, False])
            default_value = random.choice([True, False])

        elif attribute_type == "integer":
            min_value = random.randint(0, 50)
            max_value = random.randint(51, 100)
            domain = Domain(ranges=[Range(min_value, max_value)], elements=None)
            default_value = random.randint(min_value, max_value)

        elif attribute_type == "real":
            min_value = random.randint(0, 50)
            max_value = random.randint(51, 100)
            domain = Domain(ranges=[Range(min_value, max_value)], elements=None)
            default_value = round(random.uniform(min_value, max_value), 2)

        else:
            min_length = 1
            max_length = 50
            domain = Domain(ranges=[Range(min_length, max_length)], elements=None)
            length = random.randint(min_length, max_length)
            letters = string.ascii_letters + string.digits
            default_value = "".join(random.choices(letters, k=length))

        attribute = Attribute(
            name=attribute_name,
            domain=domain,
            default_value=default_value,
        )
        setattr(attribute, "attribute_type", attribute_type)

        return attribute

    def _assign_manual_attributes(self, features: list[Feature]) -> None:
        if self.model.attributes.min_attributes is not None or self.model.attributes.max_attributes is not None:
            raise ValueError("[ERROR] min_attributes and max_attributes must be None " "when using manual attributes.")

        for attribute_dict in self.model.attributes.attributes_list:
            attribute_type = (attribute_dict.get("type", "") or "").strip().lower()

            if attribute_type not in {"boolean", "integer", "real", "string"}:
                continue

            for feature in features:
                attach_probability = float(attribute_dict.get("attach_probability", 1.0))

                if random.random() >= attach_probability:
                    continue

                attribute = self._create_manual_attribute(attribute_dict, attribute_type)
                attribute.set_parent(feature)
                feature.add_attribute(attribute)

    def _create_manual_attribute(
        self,
        attribute_dict: dict,
        attribute_type: str,
    ) -> Attribute:
        name = attribute_dict.get("name")
        value = attribute_dict.get("value")
        min_value = attribute_dict.get("min_value")
        max_value = attribute_dict.get("max_value")

        if attribute_type == "boolean":
            domain_values = value

            if not isinstance(domain_values, list):
                if domain_values in [True, False]:
                    domain_values = [domain_values]
                elif isinstance(domain_values, str):
                    normalized_value = domain_values.strip().lower()

                    if normalized_value == "true":
                        domain_values = [True]
                    elif normalized_value == "false":
                        domain_values = [False]
                    else:
                        domain_values = [True, False]
                else:
                    domain_values = [True, False]

            domain = Domain(ranges=None, elements=domain_values)
            default_value = random.choice(domain_values)

        elif attribute_type == "integer":
            try:
                min_v = int(min_value)
            except Exception:
                min_v = 0

            try:
                max_v = int(max_value)
            except Exception:
                max_v = 10

            domain = Domain(ranges=[Range(min_v, max_v)], elements=None)
            default_value = random.randint(min_v, max_v)

        elif attribute_type == "real":
            try:
                min_v = float(min_value)
            except Exception:
                min_v = 0.0

            try:
                max_v = float(max_value)
            except Exception:
                max_v = 1.0

            domain = Domain(ranges=[Range(min_v, max_v)], elements=None)
            default_value = round(random.uniform(min_v, max_v), 3)

        else:
            try:
                min_length = int(min_value)
            except Exception:
                min_length = 1

            try:
                max_length = int(max_value)
            except Exception:
                max_length = 10

            domain = Domain(ranges=[Range(min_length, max_length)], elements=None)
            length = random.randint(min_length, max_length)
            letters = string.ascii_letters + string.digits
            default_value = "".join(random.choices(letters, k=length))

        attribute = Attribute(
            name=name,
            domain=domain,
            default_value=default_value,
        )
        setattr(attribute, "attribute_type", attribute_type)

        return attribute

    # -------------------------------------------------------------------------
    # Constraint pools
    # -------------------------------------------------------------------------

    def _constraints_must_be_boolean_only(self) -> bool:
        return self.model.ensure_satisfiable

    def _infer_attribute_type(self, attribute: Attribute) -> str:
        raw_attribute_type = getattr(attribute, "attribute_type", None)

        if raw_attribute_type is not None:
            return getattr(raw_attribute_type, "value", str(raw_attribute_type)).lower()

        domain = getattr(attribute, "domain", None)
        elements = getattr(domain, "elements", None) or []
        ranges = getattr(domain, "ranges", None) or []

        if elements:
            return "boolean"

        if ranges:
            range_ = ranges[0]
            range_min = getattr(range_, "min_value", None)
            range_max = getattr(range_, "max_value", None)

            if isinstance(range_min, int) and isinstance(range_max, int):
                return "integer"

            if isinstance(range_min, float) or isinstance(range_max, float):
                return "real"

            return "string"

        return "string"

    def _get_manual_attribute_config(
        self,
        attribute: Attribute,
        feature: Feature,
    ) -> tuple[str | None, bool, float, bool]:
        for attribute_dict in self.model.attributes.attributes_list:
            if attribute_dict.get("name") == attribute.name and feature.name and attribute.name:
                attribute_type = (attribute_dict.get("type", "") or "").lower()
                use_in_constraints = attribute_dict.get("use_in_constraints", False)
                constraint_probability = float(attribute_dict.get("attach_probability", 1.0))
                return (
                    attribute_type,
                    use_in_constraints,
                    constraint_probability,
                    True,
                )

        return None, False, 1.0, False

    def _should_include_attribute_in_pool(
        self,
        attribute_type: str,
        is_manual_attribute: bool,
    ) -> bool:
        if attribute_type in ("integer", "real"):
            return self.model.levels.arithmetic_level

        if attribute_type == "string":
            if is_manual_attribute:
                return True

            return self.model.levels.type_level and self.model.levels.string_constraints

        return attribute_type == "boolean"

    def _build_attribute_pools(
        self,
        features: list[Feature],
    ) -> tuple[
        list[tuple[Feature, Attribute, float]],
        list[tuple[Feature, Attribute, float]],
        list[tuple[Feature, Attribute, float]],
    ]:
        attrs_bool: list[tuple[Feature, Attribute, float]] = []
        attrs_num: list[tuple[Feature, Attribute, float]] = []
        attrs_str: list[tuple[Feature, Attribute, float]] = []

        if self._constraints_must_be_boolean_only():
            return attrs_bool, attrs_num, attrs_str

        for feature in features:
            for attribute in getattr(feature, "attributes", []):
                (
                    attribute_type,
                    use_in_constraints,
                    constraint_probability,
                    is_manual_attribute,
                ) = self._get_manual_attribute_config(attribute, feature)

                if attribute_type is None:
                    attribute_type = self._infer_attribute_type(attribute)
                    use_in_constraints = True
                    constraint_probability = RANDOM_ATTR_CONSTRAINT_PROB

                if not use_in_constraints:
                    continue

                if not self._should_include_attribute_in_pool(
                    attribute_type,
                    is_manual_attribute,
                ):
                    continue

                constraint_probability = max(
                    0.0,
                    min(float(constraint_probability), 1.0),
                )

                attribute_tuple = (feature, attribute, constraint_probability)

                if attribute_type == "boolean":
                    attrs_bool.append(attribute_tuple)
                elif attribute_type in ("integer", "real"):
                    attrs_num.append(attribute_tuple)
                elif attribute_type == "string":
                    attrs_str.append(attribute_tuple)

        return attrs_bool, attrs_num, attrs_str

    def _build_feature_pools(
        self,
        features: list[Feature],
    ) -> tuple[list[Feature], list[Feature], list[Feature]]:
        feats_bool = [feature for feature in features if self._feature_constraint_bucket(feature) == "bool"]

        if self._constraints_must_be_boolean_only():
            return feats_bool, [], []

        feats_num = [feature for feature in features if self._feature_constraint_bucket(feature) == "num"]

        feats_str = [feature for feature in features if self._feature_constraint_bucket(feature) == "string"]

        return feats_bool, feats_num, feats_str

    def _build_constraint_pools(
        self,
        features: list[Feature],
    ) -> tuple[
        list[Feature],
        list[Feature],
        list[Feature],
        list[tuple[Feature, Attribute, float]],
        list[tuple[Feature, Attribute, float]],
        list[tuple[Feature, Attribute, float]],
    ]:
        feats_bool, feats_num, feats_str = self._build_feature_pools(features)
        attrs_bool, attrs_num, attrs_str = self._build_attribute_pools(features)

        return feats_bool, feats_num, feats_str, attrs_bool, attrs_num, attrs_str

    # -------------------------------------------------------------------------
    # Constraint sampling
    # -------------------------------------------------------------------------

    def _feature_id_from_key(self, key: str) -> str:
        return key.split(".", 1)[0]

    def _group_keys_by_feature(self, keys: list[str]) -> dict[str, list[str]]:
        groups: dict[str, list[str]] = {}

        # Elimina duplicados y estabiliza el orden entre ejecuciones.
        for key in sorted(set(keys)):
            feature_id = self._feature_id_from_key(key)
            groups.setdefault(feature_id, []).append(key)

        return groups

    def _sample_keys_with_ecr(
        self,
        groups: dict[str, list[str]],
        target_occurrences: int,
        max_repetitions: int,
        max_features_param: int,
        feature_usage: dict[str, int] | None = None,
        selected_features: set[str] | None = None,
    ) -> list[str] | None:
        if target_occurrences < 1:
            return None

        feature_usage = {} if feature_usage is None else feature_usage
        selected_features = set() if selected_features is None else selected_features

        selected_keys: list[str] = []

        for _ in range(target_occurrences):
            allowed_feature_ids = [
                feature_id
                for feature_id in groups
                if feature_usage.get(feature_id, 0) < max_repetitions
                and (feature_id in selected_features or len(selected_features) < max_features_param)
            ]

            if not allowed_feature_ids:
                return None

            feature_id = random.choice(allowed_feature_ids)
            selected_keys.append(random.choice(groups[feature_id]))
            feature_usage[feature_id] = feature_usage.get(feature_id, 0) + 1
            selected_features.add(feature_id)

        random.shuffle(selected_keys)
        return selected_keys

    def _filter_attrs_for_constraint(
        self,
        attribute_pool: list[tuple[Feature, Attribute, float]],
    ) -> list[tuple[Feature, Attribute]]:
        filtered: list[tuple[Feature, Attribute]] = []

        for feature, attribute, probability in attribute_pool:
            if random.random() < probability:
                filtered.append((feature, attribute))

        return filtered

    def _ensure_non_empty_filtered_pool(
        self,
        filtered_pool: list[tuple[Feature, Attribute]],
        original_pool: list[tuple[Feature, Attribute, float]],
    ) -> list[tuple[Feature, Attribute]]:
        if filtered_pool or not original_pool:
            return filtered_pool

        weights = [max(0.0, probability) for _, _, probability in original_pool]

        if sum(weights) <= 0.0:
            return []

        feature, attribute, _ = random.choices(original_pool, weights=weights, k=1)[0]
        return [(feature, attribute)]

    def _filter_len_groups_for_numeric_use(
        self,
        len_groups: dict[str, list[str]],
        len_probability: float,
    ) -> dict[str, list[str]]:
        filtered: dict[str, list[str]] = {}

        if len_probability <= 0.0:
            return filtered

        for feature_id, values in len_groups.items():
            selected_values = [value for value in values if random.random() < len_probability]

            if selected_values:
                filtered[feature_id] = selected_values

        return filtered

    def _distinct_feature_cap(
        self,
        groups: dict[str, list[str]],
        max_features_param: int,
    ) -> int:
        return min(len(groups), max_features_param)

    def _max_occurrences_possible(
        self,
        groups: dict[str, list[str]],
        max_features_param: int,
        max_repetitions: int,
    ) -> int:
        return self._distinct_feature_cap(groups, max_features_param) * max_repetitions

    # -------------------------------------------------------------------------
    # Constraint predicates
    # -------------------------------------------------------------------------

    def _pick_bool_op(self) -> ASTOperation:
        operations = [
            ASTOperation.AND,
            ASTOperation.OR,
            ASTOperation.IMPLIES,
            ASTOperation.EQUIVALENCE,
        ]

        weights = [
            self.model.constraints.prob_and,
            self.model.constraints.prob_or_ct,
            self.model.constraints.prob_implication,
            self.model.constraints.prob_equivalence,
        ]

        return random.choices(operations, weights=weights, k=1)[0]

    def _maybe_not(self, node: Node) -> Node:
        if random.random() < self.model.constraints.prob_not:
            return Node(ASTOperation.NOT, node)

        return node

    def _build_left_deep_bool_ast(self, nodes: list[Node]) -> Node:
        if len(nodes) < 2:
            raise ValueError("[ERROR] At least two nodes are required.")

        current = Node(self._pick_bool_op(), nodes[0], nodes[1])

        for node in nodes[2:]:
            current = Node(self._pick_bool_op(), current, node)

        return current

    def _build_boolean_predicate(self, keys: list[str]) -> Node | None:
        if not keys:
            return None

        # Avoid trivial boolean constraints such as (F1 == F1)
        keys = list(dict.fromkeys(keys))

        literals = [self._maybe_not(Node(key)) for key in keys]

        if len(literals) == 1:
            return literals[0]

        return self._build_left_deep_bool_ast(literals)

    def _pick_binary_arith_op(self) -> ASTOperation:
        operations = [
            ASTOperation.ADD,
            ASTOperation.SUB,
            ASTOperation.MUL,
            ASTOperation.DIV,
        ]

        weights = [
            self.model.constraints.prob_sum,
            self.model.constraints.prob_substract,
            self.model.constraints.prob_multiply,
            self.model.constraints.prob_divide,
        ]

        if sum(weights) <= 0.0:
            return ASTOperation.ADD

        return random.choices(operations, weights=weights, k=1)[0]

    def _pick_cmp_op(self) -> ASTOperation:
        operations = [
            ASTOperation.EQUALS,
            ASTOperation.LOWER,
            ASTOperation.GREATER,
            ASTOperation.LOWER_EQUALS,
            ASTOperation.GREATER_EQUALS,
        ]

        weights = [
            self.model.constraints.prob_equals,
            self.model.constraints.prob_less,
            self.model.constraints.prob_greater,
            self.model.constraints.prob_less_equals,
            self.model.constraints.prob_greater_equals,
        ]

        return random.choices(operations, weights=weights, k=1)[0]

    def _pick_aggregate_name(self) -> str | None:
        if not self.model.levels.aggregate_functions:
            return None

        prob_sum_function = self.model.constraints.prob_sum_function
        prob_avg_function = self.model.constraints.prob_avg_function

        total = prob_sum_function + prob_avg_function

        if total <= 0.0:
            return None

        return random.choices(
            ["sum", "avg"],
            weights=[prob_sum_function, prob_avg_function],
            k=1,
        )[0]

    def _build_function_node(
        self,
        function_name: str,
        keys: list[str],
    ) -> Node:
        if len(keys) > 2:
            keys = keys[:2]

        args = ", ".join(keys)

        return Node(f"{function_name}({args})")

    def _maybe_wrap_key_with_len(
        self,
        key: str,
        len_eligible_keys: set[str],
    ) -> str:
        if key in len_eligible_keys:
            return f"len({key})"

        return key

    def _build_function_style_node(self, expression: str) -> Node:
        return Node(expression)

    def _build_plain_arith_expr(
        self,
        keys: list[str],
        len_eligible_keys: set[str] | None = None,
    ) -> Node:
        len_eligible_keys = len_eligible_keys or set()

        first_key = self._maybe_wrap_key_with_len(keys[0], len_eligible_keys)
        current = self._build_function_style_node(first_key)

        for key in keys[1:]:
            wrapped_key = self._maybe_wrap_key_with_len(key, len_eligible_keys)
            current = Node(
                self._pick_binary_arith_op(),
                current,
                self._build_function_style_node(wrapped_key),
            )

        return current

    def _maybe_wrap_with_aggregate(
        self,
        expression: Node,
        keys: list[str],
    ) -> Node:

        if not self.model.levels.aggregate_functions:
            return expression

        if len(keys) < 2:
            return expression

        aggregate_total = self.model.constraints.prob_sum_function + self.model.constraints.prob_avg_function

        if aggregate_total <= 0.0:
            return expression

        use_aggregate = random.random() < min(aggregate_total, 1.0)

        if not use_aggregate:
            return expression

        aggregate_name = self._pick_aggregate_name()

        if aggregate_name is None:
            return expression

        return self._build_function_node(
            aggregate_name,
            keys,
        )

    def _build_arith_expr(
        self,
        keys: list[str],
        len_eligible_keys: set[str] | None = None,
    ) -> Node:
        len_eligible_keys = len_eligible_keys or set()

        aggregate_total = self.model.constraints.prob_sum_function + self.model.constraints.prob_avg_function

        binary_total = (
            self.model.constraints.prob_sum
            + self.model.constraints.prob_substract
            + self.model.constraints.prob_multiply
            + self.model.constraints.prob_divide
        )

        # Si hay candidatos len(), no permitimos aggregate
        # porque produciría avg(len(...)) o sum(len(...))
        has_len_candidate = any(key in len_eligible_keys for key in keys)

        if (
            self.model.levels.aggregate_functions
            and not has_len_candidate
            and len(keys) >= 2
            and aggregate_total > 0.0
            and binary_total <= 0.0
        ):
            aggregate_name = self._pick_aggregate_name()

            if aggregate_name is not None:
                return self._build_function_node(
                    aggregate_name,
                    keys,
                )

        # Siempre construimos expresión aritmética normal.
        # Aquí len() puede mezclarse con variables numéricas.
        expression = self._build_plain_arith_expr(
            keys,
            len_eligible_keys,
        )

        # Solo aplicamos aggregate si no hay len()
        if has_len_candidate:
            return expression

        return self._maybe_wrap_with_aggregate(
            expression,
            keys,
        )

    def _build_numeric_predicate(
        self,
        keys: list[str],
        len_eligible_keys: set[str] | None = None,
    ) -> Node | None:
        if len(keys) < 2:
            return None

        len_eligible_keys = len_eligible_keys or set()

        # Avoid trivial comparisons such as (F2 < F2).
        # The same key can appear due to ECR, but both sides of a
        # comparison must reference different operands.
        unique_keys = list(dict.fromkeys(keys))

        if len(unique_keys) < 2:
            return None

        random.shuffle(unique_keys)

        split = random.randint(1, len(unique_keys) - 1)

        left_keys = unique_keys[:split]
        right_keys = unique_keys[split:]

        if not left_keys or not right_keys:
            return None

        expression_left = self._build_arith_expr(left_keys, len_eligible_keys)
        expression_right = self._build_arith_expr(right_keys, len_eligible_keys)

        return Node(self._pick_cmp_op(), expression_left, expression_right)

    def _build_string_predicate(self, keys: list[str]) -> Node | None:
        if len(keys) < 2:
            return None

        len_probability = self.model.constraints.prob_len_function

        use_len = (
            self.model.levels.type_level
            and self.model.levels.string_constraints
            and len_probability > 0.0
            and random.random() < len_probability
        )

        if use_len:
            return self._build_numeric_predicate(
                keys,
                set(keys),
            )

        if len(keys) == 2:
            return Node(ASTOperation.EQUALS, Node(keys[0]), Node(keys[1]))

        equality_nodes: list[Node] = []
        index = 0

        while index + 1 < len(keys):
            equality_nodes.append(Node(ASTOperation.EQUALS, Node(keys[index]), Node(keys[index + 1])))
            index += 2

        if not equality_nodes:
            return None

        if len(equality_nodes) == 1:
            return equality_nodes[0]

        return self._build_left_deep_bool_ast(equality_nodes)

    def _pick_predicate_kind(self, available_kinds: list[str]) -> str:
        weights: list[float] = []

        for kind in available_kinds:
            if kind == "bool":
                weights.append(self.model.constraints.ctc_dist_boolean)
            elif kind == "num":
                weights.append(self.model.constraints.ctc_dist_integer + self.model.constraints.ctc_dist_real)
            elif kind == "string":
                weights.append(self.model.constraints.ctc_dist_string)
            else:
                weights.append(0.0)

        if sum(weights) <= 0.0:
            return random.choice(available_kinds)

        return random.choices(available_kinds, weights=weights, k=1)[0]

    def _build_mixed_constraint(
        self,
        bool_groups: dict[str, list[str]],
        num_groups: dict[str, list[str]],
        str_groups: dict[str, list[str]],
        numeric_len_groups: dict[str, list[str]],
        target_occurrences: int,
        max_repetitions: int,
        max_features_param: int,
    ) -> Node | None:
        if target_occurrences < 1:
            return None

        for _ in range(50):
            remaining = target_occurrences
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
                    kind = self._pick_predicate_kind(available_kinds)

                if kind == "bool":
                    occurrences = random.randint(1, min(3, remaining))
                    chosen = self._sample_keys_with_ecr(
                        bool_groups,
                        occurrences,
                        max_repetitions,
                        max_features_param,
                        feature_usage,
                        selected_features,
                    )

                    if not chosen:
                        break

                    node = self._build_boolean_predicate(chosen)

                elif kind == "num":
                    max_occurrences = min(4, remaining)

                    if max_occurrences < 2:
                        break

                    occurrences = random.randint(2, max_occurrences)

                    numeric_groups = dict(num_groups)

                    for feature_id, values in numeric_len_groups.items():
                        numeric_groups.setdefault(feature_id, []).extend(values)

                    chosen = self._sample_keys_with_ecr(
                        numeric_groups,
                        occurrences,
                        max_repetitions,
                        max_features_param,
                        feature_usage,
                        selected_features,
                    )

                    if not chosen:
                        break

                    len_eligible_keys: set[str] = set()

                    for values in numeric_len_groups.values():
                        len_eligible_keys.update(values)

                    node = self._build_numeric_predicate(chosen, len_eligible_keys)

                else:
                    max_occurrences = min(4, remaining)

                    if max_occurrences < 2:
                        break

                    occurrences = random.randint(2, max_occurrences)

                    chosen = self._sample_keys_with_ecr(
                        str_groups,
                        occurrences,
                        max_repetitions,
                        max_features_param,
                        feature_usage,
                        selected_features,
                    )

                    if not chosen:
                        break

                    node = self._build_string_predicate(chosen)

                if node is None:
                    break

                predicate_nodes.append(node)
                remaining -= occurrences

            if remaining == 0 and predicate_nodes:
                if len(predicate_nodes) == 1:
                    return predicate_nodes[0]

                return self._build_left_deep_bool_ast(predicate_nodes)

        return None

    # -------------------------------------------------------------------------
    # Constraint generation
    # -------------------------------------------------------------------------

    def _add_constraints(
        self,
        fm: FeatureModel,
        features: list[Feature],
    ) -> None:
        boolean_only_constraints = self._constraints_must_be_boolean_only()

        (
            feats_bool,
            feats_num,
            feats_str,
            attrs_bool,
            attrs_num,
            attrs_str,
        ) = self._build_constraint_pools(features)

        min_vars = max(1, self.model.constraints.min_vars_per_constraint)
        max_vars = max(1, self.model.constraints.max_vars_per_constraint)

        if min_vars > max_vars:
            min_vars = max_vars

        max_repetitions = max(
            1,
            self.model.constraints.extra_constraint_representativeness,
        )
        max_repetitions = min(max_repetitions, max_vars)

        max_features_param = max(1, self.model.features.max_features)

        total_constraints = random.randint(
            self.model.constraints.min_constraints,
            self.model.constraints.max_constraints,
        )

        for index in range(total_constraints):
            filtered_bool_attrs = self._ensure_non_empty_filtered_pool(
                self._filter_attrs_for_constraint(attrs_bool),
                attrs_bool,
            )
            filtered_num_attrs = self._ensure_non_empty_filtered_pool(
                self._filter_attrs_for_constraint(attrs_num),
                attrs_num,
            )
            filtered_str_attrs = self._ensure_non_empty_filtered_pool(
                self._filter_attrs_for_constraint(attrs_str),
                attrs_str,
            )

            bool_pool = [feature.name for feature in feats_bool] + [
                f"{feature.name}.{attribute.name}" for feature, attribute in filtered_bool_attrs
            ]

            num_pool = [feature.name for feature in feats_num] + [
                f"{feature.name}.{attribute.name}" for feature, attribute in filtered_num_attrs
            ]

            str_pool = [feature.name for feature in feats_str] + [
                f"{feature.name}.{attribute.name}" for feature, attribute in filtered_str_attrs
            ]

            bool_groups = self._group_keys_by_feature(bool_pool)
            num_groups = self._group_keys_by_feature(num_pool)
            str_groups = self._group_keys_by_feature(str_pool)

            len_pool: list[str] = []

            if not boolean_only_constraints and self.model.levels.type_level and self.model.levels.string_constraints:
                len_pool.extend([feature.name for feature in feats_str])
                len_pool.extend(f"{feature.name}.{attribute.name}" for feature, attribute in filtered_str_attrs)

            len_groups = self._group_keys_by_feature(len_pool)
            numeric_len_groups = self._filter_len_groups_for_numeric_use(
                len_groups,
                self.model.constraints.prob_len_function,
            )

            total_capacity = 0

            if bool_groups:
                total_capacity += self._max_occurrences_possible(
                    bool_groups,
                    max_features_param,
                    max_repetitions,
                )

            if num_groups:
                total_capacity += self._max_occurrences_possible(
                    num_groups,
                    max_features_param,
                    max_repetitions,
                )

            if str_groups:
                total_capacity += self._max_occurrences_possible(
                    str_groups,
                    max_features_param,
                    max_repetitions,
                )

            if numeric_len_groups:
                total_capacity += self._max_occurrences_possible(
                    numeric_len_groups,
                    max_features_param,
                    max_repetitions,
                )

            effective_max = min(max_vars, total_capacity)
            effective_min = min_vars

            if effective_max < effective_min:
                continue

            target_occurrences = random.randint(effective_min, effective_max)

            if boolean_only_constraints:
                if not bool_groups:
                    continue

                bool_capacity = self._max_occurrences_possible(
                    bool_groups,
                    max_features_param,
                    max_repetitions,
                )

                effective_max = min(max_vars, bool_capacity)
                effective_min = min_vars

                if effective_max < effective_min:
                    continue

                target_occurrences = random.randint(effective_min, effective_max)

                chosen = self._sample_keys_with_ecr(
                    bool_groups,
                    target_occurrences,
                    max_repetitions,
                    max_features_param,
                )

                if not chosen:
                    continue

                root = self._build_boolean_predicate(chosen)

            else:
                root = self._build_mixed_constraint(
                    bool_groups,
                    num_groups,
                    str_groups,
                    numeric_len_groups,
                    target_occurrences,
                    max_repetitions,
                    max_features_param,
                )

            if root is None:
                continue

            fm.ctcs.append(Constraint(name=f"ctc{index}", ast=AST(root)))
