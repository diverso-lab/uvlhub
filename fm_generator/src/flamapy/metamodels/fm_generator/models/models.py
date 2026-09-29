from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, TYPE_CHECKING

from flamapy.core.models import VariabilityModel

if TYPE_CHECKING:
    from flamapy.metamodels.fm_metamodel.models.feature_model import Attribute


def _as_int(value: Any, default: int = 1) -> int:
    if isinstance(value, list):
        value = value[0] if value else default
    if value is None or value == "":
        return default
    return int(value)


def _as_float(value: Any, default: float = 0.0) -> float:
    if isinstance(value, list):
        value = value[0] if value else default
    if value is None or value == "":
        return default
    return float(value)


def _as_bool(value: Any, default: bool = False) -> bool:
    if isinstance(value, list):
        value = value[0] if value else default

    if isinstance(value, bool):
        return value

    if value is None or value == "":
        return default

    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "1", "yes", "y", "on", "si", "sí"}:
            return True
        if normalized in {"false", "0", "no", "n", "off"}:
            return False

    return bool(value)


def _validate_probability(value: float, name: str) -> None:
    if value < 0.0 or value > 1.0:
        raise ValueError(f"[ERROR] {name} must be between 0 and 1.")


def _validate_distribution(values: list[float], error_message: str) -> None:
    if any(value < 0.0 or value > 1.0 for value in values):
        raise ValueError("[ERROR] Distribution probabilities must be between 0 and 1.")

    total = sum(values)
    if abs(total - 1.0) > 1e-6:
        raise ValueError(f"{error_message} (actual: {total}).")


@dataclass
class NamingConfig:
    name_prefix: str = "fm"
    include_feature_count_suffix: bool = False
    include_constraint_count_suffix: bool = False

    def __post_init__(self) -> None:
        self.name_prefix = str(self.name_prefix or "fm")
        self.include_feature_count_suffix = _as_bool(self.include_feature_count_suffix)
        self.include_constraint_count_suffix = _as_bool(self.include_constraint_count_suffix)

    def validate(self) -> None:
        if not self.name_prefix.strip():
            raise ValueError("[ERROR] name_prefix cannot be empty.")


@dataclass
class LevelConfig:
    boolean_level: bool = True
    arithmetic_level: bool = False
    type_level: bool = False
    group_cardinality: bool = False
    feature_cardinality: bool = False
    aggregate_functions: bool = False
    string_constraints: bool = False

    def __post_init__(self) -> None:
        self.boolean_level = _as_bool(self.boolean_level, True)
        self.arithmetic_level = _as_bool(self.arithmetic_level)
        self.type_level = _as_bool(self.type_level)
        self.group_cardinality = _as_bool(self.group_cardinality)
        self.feature_cardinality = _as_bool(self.feature_cardinality)
        self.aggregate_functions = _as_bool(self.aggregate_functions)
        self.string_constraints = _as_bool(self.string_constraints)

    def validate(self) -> None:
        if not self.boolean_level:
            raise ValueError("[ERROR] boolean_level must always be enabled.")


@dataclass
class FeaturesConfig:
    min_features: int = 10
    max_features: int = 50

    dist_boolean: float = 0.7
    dist_integer: float = 0.1
    dist_real: float = 0.1
    dist_string: float = 0.1

    min_feature_cardinality: int | list[int] = 2
    max_feature_cardinality: int | list[int] = 5
    prob_feature_cardinality: float = 0.1

    def __post_init__(self) -> None:
        self.min_features = _as_int(self.min_features, 10)
        self.max_features = _as_int(self.max_features, 50)

        self.dist_boolean = _as_float(self.dist_boolean, 0.7)
        self.dist_integer = _as_float(self.dist_integer, 0.1)
        self.dist_real = _as_float(self.dist_real, 0.1)
        self.dist_string = _as_float(self.dist_string, 0.1)

        self.min_feature_cardinality = _as_int(self.min_feature_cardinality, 2)
        self.max_feature_cardinality = _as_int(self.max_feature_cardinality, 5)
        self.prob_feature_cardinality = _as_float(self.prob_feature_cardinality, 0.1)

    def validate(self, levels: LevelConfig) -> None:
        if self.min_features < 1 or self.max_features < 1:
            raise ValueError("[ERROR] Feature limits must be at least 1.")

        if self.min_features > self.max_features:
            raise ValueError("[ERROR] min_features cannot be greater than max_features.")

        _validate_distribution(
            [
                self.dist_boolean,
                self.dist_integer,
                self.dist_real,
                self.dist_string,
            ],
            "[ERROR] Attribute type probabilities must sum to 1.0",
        )

        if levels.feature_cardinality:
            if self.min_feature_cardinality < 1 or self.max_feature_cardinality < 1:
                raise ValueError("[ERROR] Feature cardinality bounds must be at least 1.")

            if self.min_feature_cardinality > self.max_feature_cardinality:
                raise ValueError(
                    "[ERROR] min_feature_cardinality cannot be greater than max_feature_cardinality."
                )

            _validate_probability(
                self.prob_feature_cardinality,
                "prob_feature_cardinality",
            )


@dataclass
class HierarchyConfig:
    max_tree_depth: int = 5

    dist_optional: float = 0.3
    dist_mandatory: float = 0.3
    dist_alternative: float = 0.2
    dist_or: float = 0.2

    group_cardinality_min: int = 1
    group_cardinality_max: int = 6
    dist_group_cardinality: float = 0.0

    def __post_init__(self) -> None:
        self.max_tree_depth = _as_int(self.max_tree_depth, 5)

        self.dist_optional = _as_float(self.dist_optional, 0.3)
        self.dist_mandatory = _as_float(self.dist_mandatory, 0.3)
        self.dist_alternative = _as_float(self.dist_alternative, 0.2)
        self.dist_or = _as_float(self.dist_or, 0.2)

        self.group_cardinality_min = _as_int(self.group_cardinality_min, 1)
        self.group_cardinality_max = _as_int(self.group_cardinality_max, 6)
        self.dist_group_cardinality = _as_float(self.dist_group_cardinality, 0.0)

    def validate(self, features: FeaturesConfig, levels: LevelConfig) -> None:
        if not (1 <= self.max_tree_depth <= features.max_features):
            raise ValueError("[ERROR] max_tree_depth must be between 1 and max_features.")

        _validate_distribution(
            [
                self.dist_optional,
                self.dist_mandatory,
                self.dist_alternative,
                self.dist_or,
                self.dist_group_cardinality,
            ],
            "[ERROR] Relation probabilities must sum to 1.0",
        )

        if levels.group_cardinality:
            if self.group_cardinality_min < 1 or self.group_cardinality_max < 1:
                raise ValueError("[ERROR] Group cardinality bounds must be at least 1.")

            if self.group_cardinality_min > self.group_cardinality_max:
                raise ValueError(
                    "[ERROR] group_cardinality_min cannot be greater than group_cardinality_max."
                )


@dataclass
class ConstraintsConfig:
    min_constraints: int = 5
    max_constraints: int = 20
    extra_constraint_representativeness: int = 1
    min_vars_per_constraint: int = 1
    max_vars_per_constraint: int = 3

    ctc_dist_boolean: float = 0.7
    ctc_dist_integer: float = 0.2
    ctc_dist_real: float = 0.1
    ctc_dist_string: float = 0.0

    prob_not: float = 0.1
    prob_and: float = 0.4
    prob_or_ct: float = 0.2
    prob_implication: float = 0.2
    prob_equivalence: float = 0.2

    prob_sum: float = 0.7
    prob_substract: float = 0.2
    prob_multiply: float = 0.1
    prob_divide: float = 0.0

    prob_equals: float = 0.1
    prob_less: float = 0.2
    prob_greater: float = 0.7
    prob_less_equals: float = 0.0
    prob_greater_equals: float = 0.0

    prob_sum_function: float = 0.0
    prob_avg_function: float = 0.0
    prob_len_function: float = 0.0

    def __post_init__(self) -> None:
        self.min_constraints = _as_int(self.min_constraints, 5)
        self.max_constraints = _as_int(self.max_constraints, 20)
        self.extra_constraint_representativeness = _as_int(
            self.extra_constraint_representativeness,
            1,
        )
        self.min_vars_per_constraint = _as_int(self.min_vars_per_constraint, 1)
        self.max_vars_per_constraint = _as_int(self.max_vars_per_constraint, 3)

        self.ctc_dist_boolean = _as_float(self.ctc_dist_boolean, 0.7)
        self.ctc_dist_integer = _as_float(self.ctc_dist_integer, 0.2)
        self.ctc_dist_real = _as_float(self.ctc_dist_real, 0.1)
        self.ctc_dist_string = _as_float(self.ctc_dist_string, 0.0)

        self.prob_not = _as_float(self.prob_not, 0.1)
        self.prob_and = _as_float(self.prob_and, 0.4)
        self.prob_or_ct = _as_float(self.prob_or_ct, 0.2)
        self.prob_implication = _as_float(self.prob_implication, 0.2)
        self.prob_equivalence = _as_float(self.prob_equivalence, 0.2)

        self.prob_sum = _as_float(self.prob_sum, 0.7)
        self.prob_substract = _as_float(self.prob_substract, 0.2)
        self.prob_multiply = _as_float(self.prob_multiply, 0.1)
        self.prob_divide = _as_float(self.prob_divide, 0.0)

        self.prob_equals = _as_float(self.prob_equals, 0.1)
        self.prob_less = _as_float(self.prob_less, 0.2)
        self.prob_greater = _as_float(self.prob_greater, 0.7)
        self.prob_less_equals = _as_float(self.prob_less_equals, 0.0)
        self.prob_greater_equals = _as_float(self.prob_greater_equals, 0.0)

        self.prob_sum_function = _as_float(self.prob_sum_function, 0.0)
        self.prob_avg_function = _as_float(self.prob_avg_function, 0.0)
        self.prob_len_function = _as_float(self.prob_len_function, 0.0)

    def validate(self, levels: LevelConfig) -> None:
        self._validate_basic_ranges()
        self._validate_constraint_type_distribution(levels)
        self._validate_boolean_distribution()
        self._validate_arithmetic_distribution(levels)

    def _validate_basic_ranges(self) -> None:
        if self.min_constraints < 1 or self.max_constraints < 1:
            raise ValueError("[ERROR] Constraint limits must be at least 1.")

        if self.min_constraints > self.max_constraints:
            raise ValueError("[ERROR] min_constraints cannot be greater than max_constraints.")

        if self.extra_constraint_representativeness < 1:
            raise ValueError("[ERROR] extra_constraint_representativeness must be at least 1.")

        if self.min_vars_per_constraint < 1 or self.max_vars_per_constraint < 1:
            raise ValueError("[ERROR] Vars per constraint must be at least 1.")

        if self.min_vars_per_constraint > self.max_vars_per_constraint:
            raise ValueError(
                "[ERROR] min_vars_per_constraint cannot be greater than max_vars_per_constraint."
            )

    def _validate_constraint_type_distribution(self, levels: LevelConfig) -> None:
        active_values = [self.ctc_dist_boolean]

        if levels.arithmetic_level:
            active_values.extend([self.ctc_dist_integer, self.ctc_dist_real])

        if levels.type_level and levels.string_constraints:
            active_values.append(self.ctc_dist_string)

        _validate_distribution(
            active_values,
            "[ERROR] CTC type probabilities must sum to 1.0",
        )

    def _validate_boolean_distribution(self) -> None:
        _validate_probability(self.prob_not, "prob_not")

        _validate_distribution(
            [
                self.prob_and,
                self.prob_or_ct,
                self.prob_implication,
                self.prob_equivalence,
            ],
            "[ERROR] prob_and, prob_or_ct, prob_implication and prob_equivalence must sum to 1.0",
        )

    def _validate_arithmetic_distribution(self, levels: LevelConfig) -> None:
        if not levels.arithmetic_level:
            return

        operation_values = [
            self.prob_sum,
            self.prob_substract,
            self.prob_multiply,
            self.prob_divide,
        ]

        if levels.aggregate_functions:
            operation_values.extend(
                [
                    self.prob_sum_function,
                    self.prob_avg_function,
                ]
            )

        _validate_distribution(
            operation_values,
            "[ERROR] Arithmetic probabilities must sum to 1.0",
        )

        _validate_distribution(
            [
                self.prob_equals,
                self.prob_less,
                self.prob_greater,
                self.prob_less_equals,
                self.prob_greater_equals,
            ],
            "[ERROR] Comparison probabilities must sum to 1.0",
        )


@dataclass
class AttributesConfig:
    random_attributes: bool = True
    min_attributes: int | None = 1
    max_attributes: int | None = 5

    dist_boolean_atr: float = 0.7
    dist_integer_atr: float = 0.1
    dist_real_atr: float = 0.1
    dist_string_atr: float = 0.1

    attributes_list: list[Attribute | dict[str, Any]] = field(default_factory=list)
    attribute_attach_probs: list[float] = field(default_factory=list)
    attribute_in_constraints: list[bool] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.random_attributes = _as_bool(self.random_attributes, True)

        if self.min_attributes is not None and self.min_attributes != "":
            self.min_attributes = _as_int(self.min_attributes, 1)
        else:
            self.min_attributes = None

        if self.max_attributes is not None and self.max_attributes != "":
            self.max_attributes = _as_int(self.max_attributes, 5)
        else:
            self.max_attributes = None

        self.attribute_attach_probs = [
            _as_float(probability, 0.0)
            for probability in self.attribute_attach_probs
        ]

        self.attribute_in_constraints = [
            _as_bool(value)
            for value in self.attribute_in_constraints
        ]

        self.dist_boolean_atr = _as_float(
            self.dist_boolean_atr,
            0.7,
        )

        self.dist_integer_atr = _as_float(
            self.dist_integer_atr,
            0.1,
        )

        self.dist_real_atr = _as_float(
            self.dist_real_atr,
            0.1,
        )

        self.dist_string_atr = _as_float(
            self.dist_string_atr,
            0.1,
        )

    def validate(self) -> None:
        if self.random_attributes:
            _validate_distribution(
                [
                    self.dist_boolean_atr,
                    self.dist_integer_atr,
                    self.dist_real_atr,
                    self.dist_string_atr,
                ],
                "[ERROR] Attribute type probabilities must sum to 1.0",
            )

            if self.min_attributes is None or self.max_attributes is None:
                raise ValueError(
                    "[ERROR] min_attributes and max_attributes are required in random mode."
                )

            if self.min_attributes < 0 or self.max_attributes < 0:
                raise ValueError("[ERROR] Attribute limits cannot be negative.")

            if self.min_attributes > self.max_attributes:
                raise ValueError("[ERROR] min_attributes cannot be greater than max_attributes.")

        else:
            if self.min_attributes is not None or self.max_attributes is not None:
                raise ValueError(
                    "[ERROR] min_attributes and max_attributes must be None in manual mode."
                )

            for index, probability in enumerate(self.attribute_attach_probs):
                _validate_probability(
                    probability,
                    f"attribute_attach_probs[{index}]",
                )


@dataclass
class FmgeneratorModel(VariabilityModel):
    num_models: int = 1
    seed: int = 1
    ensure_satisfiable: bool = True

    naming: NamingConfig = field(default_factory=NamingConfig)
    levels: LevelConfig = field(default_factory=LevelConfig)
    features: FeaturesConfig = field(default_factory=FeaturesConfig)
    hierarchy: HierarchyConfig = field(default_factory=HierarchyConfig)
    constraints: ConstraintsConfig = field(default_factory=ConstraintsConfig)
    attributes: AttributesConfig = field(default_factory=AttributesConfig)

    @staticmethod
    def get_extension() -> str:
        return "fm"

    def __post_init__(self) -> None:
        self.num_models = _as_int(self.num_models, 1)
        self.seed = _as_int(self.seed, 1)
        self.ensure_satisfiable = _as_bool(self.ensure_satisfiable, True)

        self._coerce_nested_configs()
        self._normalize_dependencies()
        self.validate()

    def _coerce_nested_configs(self) -> None:
        if isinstance(self.naming, dict):
            self.naming = NamingConfig(**self.naming)

        if isinstance(self.levels, dict):
            self.levels = LevelConfig(**self.levels)

        if isinstance(self.features, dict):
            self.features = FeaturesConfig(**self.features)

        if isinstance(self.hierarchy, dict):
            self.hierarchy = HierarchyConfig(**self.hierarchy)

        if isinstance(self.constraints, dict):
            self.constraints = ConstraintsConfig(**self.constraints)

        if isinstance(self.attributes, dict):
            self.attributes = AttributesConfig(**self.attributes)

    def _normalize_dependencies(self) -> None:
        self.levels.boolean_level = True

        if self.levels.type_level:
            self.levels.arithmetic_level = True

        if not self.levels.arithmetic_level:
            self.levels.feature_cardinality = False
            self.levels.aggregate_functions = False
            self.constraints.ctc_dist_integer = 0.0
            self.constraints.ctc_dist_real = 0.0

        if not self.levels.type_level:
            self.levels.string_constraints = False
            self.constraints.ctc_dist_string = 0.0

        if self.ensure_satisfiable:
            self.constraints.ctc_dist_boolean = 1.0
            self.constraints.ctc_dist_integer = 0.0
            self.constraints.ctc_dist_real = 0.0
            self.constraints.ctc_dist_string = 0.0

    def validate(self) -> None:
        if self.num_models < 1:
            raise ValueError("[ERROR] num_models must be at least 1.")

        if self.seed <= 0:
            raise ValueError("[ERROR] seed must be positive.")

        self.naming.validate()
        self.levels.validate()
        self.features.validate(self.levels)
        self.hierarchy.validate(self.features, self.levels)
        self.constraints.validate(self.levels)
        self.attributes.validate()

    @classmethod
    def from_flat_dict(cls, params: dict) -> "FmgeneratorModel":
        """Build a FmgeneratorModel from the flat dictionary currently produced by UVLHub.

        This keeps the UVLHub wizard temporarily compatible with the new OO model.
        """
        return cls(
            num_models=params.get("NUM_MODELS", 1),
            seed=params.get("SEED", 1),
            ensure_satisfiable=params.get("ENSURE_SATISFIABLE", True),

            naming=NamingConfig(
                name_prefix=params.get("NAME_PREFIX", "fm"),
                include_feature_count_suffix=params.get("INCLUDE_FEATURE_COUNT_SUFFIX", False),
                include_constraint_count_suffix=params.get("INCLUDE_CONSTRAINT_COUNT_SUFFIX", False),
            ),

            levels=LevelConfig(
                boolean_level=params.get("BOOLEAN_LEVEL", True),
                arithmetic_level=params.get("ARITHMETIC_LEVEL", False),
                type_level=params.get("TYPE_LEVEL", False),
                group_cardinality=params.get("GROUP_CARDINALITY", False),
                feature_cardinality=params.get("FEATURE_CARDINALITY", False),
                aggregate_functions=params.get("AGGREGATE_FUNCTIONS", False),
                string_constraints=params.get("STRING_CONSTRAINTS", False),
            ),

            features=FeaturesConfig(
                min_features=params.get("MIN_FEATURES", 10),
                max_features=params.get("MAX_FEATURES", 50),
                dist_boolean=params.get("FEATURE_DIST_BOOLEAN", 0.7),
                dist_integer=params.get("FEATURE_DIST_INTEGER", 0.1),
                dist_real=params.get("FEATURE_DIST_REAL", 0.1),
                dist_string=params.get("FEATURE_DIST_STRING", 0.1),
                min_feature_cardinality=params.get("MIN_FEATURE_CARDINALITY", 2),
                max_feature_cardinality=params.get("MAX_FEATURE_CARDINALITY", 5),
                prob_feature_cardinality=params.get("PROB_FEATURE_CARDINALITY", 0.1),
            ),

            hierarchy=HierarchyConfig(
                max_tree_depth=params.get("MAX_TREE_DEPTH", 5),
                dist_optional=params.get("DIST_OPTIONAL", 0.3),
                dist_mandatory=params.get("DIST_MANDATORY", 0.3),
                dist_alternative=params.get("DIST_ALTERNATIVE", 0.2),
                dist_or=params.get("DIST_OR", 0.2),
                group_cardinality_min=params.get("GROUP_CARDINALITY_MIN", 1),
                group_cardinality_max=params.get("GROUP_CARDINALITY_MAX", 6),
                dist_group_cardinality=params.get("DIST_GROUP_CARDINALITY", 0.0),
            ),

            constraints=ConstraintsConfig(
                min_constraints=params.get("MIN_CONSTRAINTS", 5),
                max_constraints=params.get("MAX_CONSTRAINTS", 20),
                extra_constraint_representativeness=params.get(
                    "EXTRA_CONSTRAINT_REPRESENTATIVENESS",
                    1,
                ),
                min_vars_per_constraint=params.get("MIN_VARS_PER_CONSTRAINT", 1),
                max_vars_per_constraint=params.get("MAX_VARS_PER_CONSTRAINT", 3),

                ctc_dist_boolean=params.get("CTC_DIST_BOOLEAN", 0.7),
                ctc_dist_integer=params.get("CTC_DIST_INTEGER", 0.2),
                ctc_dist_real=params.get("CTC_DIST_REAL", 0.1),
                ctc_dist_string=params.get("CTC_DIST_STRING", 0.0),

                prob_not=params.get("PROB_NOT", 0.1),
                prob_and=params.get("PROB_AND", 0.4),
                prob_or_ct=params.get("PROB_OR_CT", 0.2),
                prob_implication=params.get("PROB_IMPLICATION", 0.2),
                prob_equivalence=params.get("PROB_EQUIVALENCE", 0.2),

                prob_sum=params.get("PROB_SUM", 0.7),
                prob_substract=params.get("PROB_SUBSTRACT", 0.2),
                prob_multiply=params.get("PROB_MULTIPLY", 0.1),
                prob_divide=params.get("PROB_DIVIDE", 0.0),

                prob_equals=params.get("PROB_EQUALS", 0.1),
                prob_less=params.get("PROB_LESS", 0.2),
                prob_greater=params.get("PROB_GREATER", 0.7),
                prob_less_equals=params.get("PROB_LESS_EQUALS", 0.0),
                prob_greater_equals=params.get("PROB_GREATER_EQUALS", 0.0),

                prob_sum_function=params.get("PROB_SUM_FUNCTION", 0.0),
                prob_avg_function=params.get("PROB_AVG_FUNCTION", 0.0),
                prob_len_function=params.get("PROB_LEN_FUNCTION", 0.0),
            ),

            attributes=AttributesConfig(
                random_attributes=params.get("RANDOM_ATTRIBUTES", True),
                min_attributes=params.get("MIN_ATTRIBUTES", 1),
                max_attributes=params.get("MAX_ATTRIBUTES", 5),
                dist_boolean_atr=params.get("ATTR_DIST_BOOLEAN", 0.7),
                dist_integer_atr=params.get("ATTR_DIST_INTEGER", 0.1),
                dist_real_atr=params.get("ATTR_DIST_REAL", 0.1),
                dist_string_atr=params.get("ATTR_DIST_STRING", 0.1),
                attributes_list=params.get("ATTRIBUTES_LIST", []),
                attribute_attach_probs=params.get("ATTRIBUTE_ATTACH_PROBS", []),
                attribute_in_constraints=params.get("ATTRIBUTE_IN_CONSTRAINTS", []),
            ),
        )
