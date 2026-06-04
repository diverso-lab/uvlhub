from dataclasses import dataclass, field
from typing import Any

from flamapy.metamodels.fm_metamodel.models.feature_model import Attribute


def _as_int(value: Any, default: int = 1) -> int:
    if isinstance(value, list):
        value = value[0] if value else default
    return int(value)


@dataclass
class Params:
    NUM_MODELS: int = 1
    SEED: int = 1
    ENSURE_SATISFIABLE: bool = True
    NAME_PREFIX: str = "fm"
    INCLUDE_FEATURE_COUNT_SUFFIX: bool = False
    INCLUDE_CONSTRAINT_COUNT_SUFFIX: bool = False

    BOOLEAN_LEVEL: bool = True
    ARITHMETIC_LEVEL: bool = False
    TYPE_LEVEL: bool = False
    GROUP_CARDINALITY: bool = False
    FEATURE_CARDINALITY: bool = False
    AGGREGATE_FUNCTIONS: bool = False
    STRING_CONSTRAINTS: bool = False

    MIN_FEATURES: int = 10
    MAX_FEATURES: int = 50
    DIST_BOOLEAN: float = 0.7
    DIST_INTEGER: float = 0.1
    DIST_REAL: float = 0.1
    DIST_STRING: float = 0.1

    MIN_FEATURE_CARDINALITY: int | list[int] = 2
    MAX_FEATURE_CARDINALITY: int | list[int] = 5
    PROB_FEATURE_CARDINALITY: float = 0.1

    MAX_TREE_DEPTH: int = 5
    DIST_OPTIONAL: float = 0.3
    DIST_MANDATORY: float = 0.3
    DIST_ALTERNATIVE: float = 0.2
    DIST_OR: float = 0.2
    GROUP_CARDINALITY_MIN: int = 1
    GROUP_CARDINALITY_MAX: int = 6
    DIST_GROUP_CARDINALITY: float = 0.0

    MIN_CONSTRAINTS: int = 5
    MAX_CONSTRAINTS: int = 20
    EXTRA_CONSTRAINT_REPRESENTATIVENESS: int = 1
    MIN_VARS_PER_CONSTRAINT: int = 1
    MAX_VARS_PER_CONSTRAINT: int = 3

    CTC_DIST_BOOLEAN: float = 0.7
    CTC_DIST_INTEGER: float = 0.2
    CTC_DIST_REAL: float = 0.1
    CTC_DIST_STRING: float = 0.0

    PROB_NOT: float = 0.1
    PROB_AND: float = 0.4
    PROB_OR_CT: float = 0.2
    PROB_IMPLICATION: float = 0.2
    PROB_EQUIVALENCE: float = 0.2

    PROB_SUM: float = 0.7
    PROB_SUBSTRACT: float = 0.2
    PROB_MULTIPLY: float = 0.1
    PROB_DIVIDE: float = 0.0

    PROB_EQUALS: float = 0.1
    PROB_LESS: float = 0.2
    PROB_GREATER: float = 0.7
    PROB_LESS_EQUALS: float = 0.0
    PROB_GREATER_EQUALS: float = 0.0
    PROB_SUM_FUNCTION: float = 0.0
    PROB_AVG_FUNCTION: float = 0.0
    PROB_LEN_FUNCTION: float = 0.0

    RANDOM_ATTRIBUTES: bool = True
    MIN_ATTRIBUTES: int | None = 1
    MAX_ATTRIBUTES: int | None = 5
    ATTRIBUTES_LIST: list[Attribute | dict] = field(default_factory=list)
    ATTRIBUTE_ATTACH_PROBS: list[float] = field(default_factory=list)
    ATTRIBUTE_IN_CONSTRAINTS: list[bool] = field(default_factory=list)

    def __post_init__(self):
        self.BOOLEAN_LEVEL = True

        self.NUM_MODELS = int(self.NUM_MODELS)
        self.SEED = int(self.SEED)
        self.MIN_FEATURES = int(self.MIN_FEATURES)
        self.MAX_FEATURES = int(self.MAX_FEATURES)
        self.MAX_TREE_DEPTH = int(self.MAX_TREE_DEPTH)
        self.MIN_CONSTRAINTS = int(self.MIN_CONSTRAINTS)
        self.MAX_CONSTRAINTS = int(self.MAX_CONSTRAINTS)
        self.EXTRA_CONSTRAINT_REPRESENTATIVENESS = int(self.EXTRA_CONSTRAINT_REPRESENTATIVENESS)
        self.MIN_VARS_PER_CONSTRAINT = int(self.MIN_VARS_PER_CONSTRAINT)
        self.MAX_VARS_PER_CONSTRAINT = int(self.MAX_VARS_PER_CONSTRAINT)

        self.MIN_FEATURE_CARDINALITY = _as_int(self.MIN_FEATURE_CARDINALITY, 2)
        self.MAX_FEATURE_CARDINALITY = _as_int(self.MAX_FEATURE_CARDINALITY, 5)

        if self.TYPE_LEVEL:
            self.ARITHMETIC_LEVEL = True

        if not self.ARITHMETIC_LEVEL:
            self.FEATURE_CARDINALITY = False
            self.AGGREGATE_FUNCTIONS = False
            self.CTC_DIST_INTEGER = 0.0
            self.CTC_DIST_REAL = 0.0

        if not self.TYPE_LEVEL:
            self.STRING_CONSTRAINTS = False
            self.CTC_DIST_STRING = 0.0

        if self.ENSURE_SATISFIABLE:
            self.CTC_DIST_BOOLEAN = 1.0
            self.CTC_DIST_INTEGER = 0.0
            self.CTC_DIST_REAL = 0.0
            self.CTC_DIST_STRING = 0.0

        self._validate_basic_ranges()
        self._validate_relation_distribution()
        self._validate_boolean_distribution()
        self._validate_type_distribution()
        self._validate_constraint_type_distribution()
        self._validate_arithmetic_distribution()
        self._validate_attributes()

    def _validate_basic_ranges(self):
        if self.NUM_MODELS < 1:
            raise ValueError("[ERROR] NUM_MODELS must be at least 1.")
        if self.SEED <= 0:
            raise ValueError("[ERROR] SEED must be positive.")
        if self.MIN_FEATURES < 1 or self.MAX_FEATURES < 1:
            raise ValueError("[ERROR] Feature limits must be at least 1.")
        if self.MIN_FEATURES > self.MAX_FEATURES:
            raise ValueError("[ERROR] MIN_FEATURES cannot be greater than MAX_FEATURES.")
        if not (1 <= self.MAX_TREE_DEPTH <= self.MAX_FEATURES):
            raise ValueError("[ERROR] MAX_TREE_DEPTH must be between 1 and MAX_FEATURES.")

        if self.MIN_CONSTRAINTS < 1 or self.MAX_CONSTRAINTS < 1:
            raise ValueError("[ERROR] Constraint limits must be at least 1.")
        if self.MIN_CONSTRAINTS > self.MAX_CONSTRAINTS:
            raise ValueError("[ERROR] MIN_CONSTRAINTS cannot be greater than MAX_CONSTRAINTS.")
        if self.EXTRA_CONSTRAINT_REPRESENTATIVENESS < 1:
            raise ValueError("[ERROR] EXTRA_CONSTRAINT_REPRESENTATIVENESS must be at least 1.")
        if self.MIN_VARS_PER_CONSTRAINT < 1 or self.MAX_VARS_PER_CONSTRAINT < 1:
            raise ValueError("[ERROR] Vars per constraint must be at least 1.")
        if self.MIN_VARS_PER_CONSTRAINT > self.MAX_VARS_PER_CONSTRAINT:
            raise ValueError("[ERROR] MIN_VARS_PER_CONSTRAINT cannot be greater than MAX_VARS_PER_CONSTRAINT.")

        if self.FEATURE_CARDINALITY:
            if self.MIN_FEATURE_CARDINALITY < 1 or self.MAX_FEATURE_CARDINALITY < 1:
                raise ValueError("[ERROR] Feature cardinality bounds must be at least 1.")
            if self.MIN_FEATURE_CARDINALITY > self.MAX_FEATURE_CARDINALITY:
                raise ValueError("[ERROR] MIN_FEATURE_CARDINALITY cannot be greater than MAX_FEATURE_CARDINALITY.")
            if not (0.0 <= self.PROB_FEATURE_CARDINALITY <= 1.0):
                raise ValueError("[ERROR] PROB_FEATURE_CARDINALITY must be between 0 and 1.")

    def _validate_relation_distribution(self):
        values = [
            self.DIST_OPTIONAL,
            self.DIST_MANDATORY,
            self.DIST_ALTERNATIVE,
            self.DIST_OR,
            self.DIST_GROUP_CARDINALITY,
        ]
        if any(v < 0.0 or v > 1.0 for v in values):
            raise ValueError("[ERROR] Relation probabilities must be between 0 and 1.")
        total = sum(values)
        if abs(total - 1.0) > 1e-6:
            raise ValueError(f"[ERROR] Relation probabilities must sum to 1.0 (actual: {total}).")

    def _validate_boolean_distribution(self):
        values = [
            self.PROB_AND,
            self.PROB_OR_CT,
            self.PROB_IMPLICATION,
            self.PROB_EQUIVALENCE,
        ]
        if any(v < 0.0 or v > 1.0 for v in values):
            raise ValueError("[ERROR] Boolean connective probabilities must be between 0 and 1.")
        total = sum(values)
        if abs(total - 1.0) > 1e-6:
            raise ValueError(
                f"[ERROR] PROB_AND, PROB_OR_CT, PROB_IMPLICATION and PROB_EQUIVALENCE must sum to 1.0 "
                f"(actual: {total})."
            )
        if not (0.0 <= self.PROB_NOT <= 1.0):
            raise ValueError("[ERROR] PROB_NOT must be between 0 and 1.")

    def _validate_type_distribution(self):
        values = [
            self.DIST_BOOLEAN,
            self.DIST_INTEGER,
            self.DIST_REAL,
            self.DIST_STRING,
        ]

        if any(v < 0.0 or v > 1.0 for v in values):
            raise ValueError("[ERROR] Attribute type probabilities must be between 0 and 1.")

        total = sum(values)
        if abs(total - 1.0) > 1e-6:
            raise ValueError(f"[ERROR] Attribute type probabilities must sum to 1.0 (actual: {total}).")

    def _validate_constraint_type_distribution(self):
        active = [self.CTC_DIST_BOOLEAN]

        if self.ARITHMETIC_LEVEL:
            active.extend([self.CTC_DIST_INTEGER, self.CTC_DIST_REAL])

        if self.TYPE_LEVEL and self.STRING_CONSTRAINTS:
            active.append(self.CTC_DIST_STRING)

        if any(v < 0.0 or v > 1.0 for v in active):
            raise ValueError("[ERROR] CTC type probabilities must be between 0 and 1.")

        total = sum(active)
        if abs(total - 1.0) > 1e-6:
            raise ValueError(f"[ERROR] CTC type probabilities must sum to 1.0 (actual: {total}).")

    def _validate_arithmetic_distribution(self):
        if not self.ARITHMETIC_LEVEL:
            return

        ops = [
            self.PROB_SUM,
            self.PROB_SUBSTRACT,
            self.PROB_MULTIPLY,
            self.PROB_DIVIDE,
        ]

        if self.AGGREGATE_FUNCTIONS:
            ops.extend([self.PROB_SUM_FUNCTION, self.PROB_AVG_FUNCTION])

        if any(v < 0.0 or v > 1.0 for v in ops):
            raise ValueError("[ERROR] Arithmetic probabilities must be between 0 and 1.")

        total = sum(ops)
        if abs(total - 1.0) > 1e-6:
            raise ValueError(f"[ERROR] Arithmetic probabilities must sum to 1.0 (actual: {total}).")

        cmp_values = [
            self.PROB_EQUALS,
            self.PROB_LESS,
            self.PROB_GREATER,
            self.PROB_LESS_EQUALS,
            self.PROB_GREATER_EQUALS,
        ]

        if any(v < 0.0 or v > 1.0 for v in cmp_values):
            raise ValueError("[ERROR] Comparison probabilities must be between 0 and 1.")

        cmp_total = sum(cmp_values)
        if abs(cmp_total - 1.0) > 1e-6:
            raise ValueError(f"[ERROR] Comparison probabilities must sum to 1.0 (actual: {cmp_total}).")

    def _validate_attributes(self):
        if self.RANDOM_ATTRIBUTES:
            if self.MIN_ATTRIBUTES is None or self.MAX_ATTRIBUTES is None:
                raise ValueError("[ERROR] MIN_ATTRIBUTES and MAX_ATTRIBUTES are required in random mode.")
            self.MIN_ATTRIBUTES = int(self.MIN_ATTRIBUTES)
            self.MAX_ATTRIBUTES = int(self.MAX_ATTRIBUTES)
            if self.MIN_ATTRIBUTES < 0 or self.MAX_ATTRIBUTES < 0:
                raise ValueError("[ERROR] Attribute limits cannot be negative.")
            if self.MIN_ATTRIBUTES > self.MAX_ATTRIBUTES:
                raise ValueError("[ERROR] MIN_ATTRIBUTES cannot be greater than MAX_ATTRIBUTES.")
        else:
            if self.MIN_ATTRIBUTES is not None or self.MAX_ATTRIBUTES is not None:
                raise ValueError("[ERROR] MIN_ATTRIBUTES and MAX_ATTRIBUTES must be None in manual mode.")

            for i, p in enumerate(self.ATTRIBUTE_ATTACH_PROBS):
                if not (0.0 <= p <= 1.0):
                    raise ValueError(f"[ERROR] Attribute attach probability at index {i} must be between 0 and 1.")
