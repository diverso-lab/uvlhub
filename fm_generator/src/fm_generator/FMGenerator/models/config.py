from dataclasses import dataclass, field
from flamapy.metamodels.fm_metamodel.models.feature_model import Attribute

@dataclass
class Params:
    # Paso 1: General
    NUM_MODELS: int = 1
    SEED: int = 1
    ENSURE_SATISFIABLE: bool = True
    NAME_PREFIX: str = "fm"
    INCLUDE_FEATURE_COUNT_SUFFIX: bool = False
    INCLUDE_CONSTRAINT_COUNT_SUFFIX: bool = False

    # Paso 2: Feature tree
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

    MIN_FEATURE_CARDINALITY: list[int] = field(default_factory=lambda: [2])
    MAX_FEATURE_CARDINALITY: list[int] = field(default_factory=lambda: [5, 8])
    PROB_FEATURE_CARDINALITY: float = 0.5

    MAX_TREE_DEPTH: int = 5
    DIST_OPTIONAL: float = 0.3
    DIST_MANDATORY: float = 0.3
    DIST_ALTERNATIVE: float = 0.2
    DIST_OR: float = 0.2
    GROUP_CARDINALITY_MIN: int = 1
    GROUP_CARDINALITY_MAX: int = 6
    DIST_GROUP_CARDINALITY: float = 0.0

    # Paso 3: Constraints
    MIN_CONSTRAINTS: int = 5
    MAX_CONSTRAINTS: int = 20
    EXTRA_CONSTRAINT_REPRESENTATIVENESS: int = 1
    MIN_VARS_PER_CONSTRAINT: int = 1
    MAX_VARS_PER_CONSTRAINT: int = 3


    # NO REFLEJADO EN EL GENERADOR AÚN
    CTC_DIST_BOOLEAN: float = 0.7
    CTC_DIST_INTEGER: float = 0.2
    CTC_DIST_REAL: float = 0.1
    CTC_DIST_STRING: float = 0.0
    # NO REFLEJADO EN EL GENERADOR AÚN


    PROB_NOT: float = 0.1
    PROB_AND: float = 0.4
    PROB_OR_CT: float = 0.2
    PROB_IMPLICATION: float = 0.2
    PROB_EQUIVALENCE: float = 0.2

    PROB_SUM: float = 0.1
    PROB_SUBSTRACT: float = 0.1
    PROB_MULTIPLY: float = 0.1
    PROB_DIVIDE: float = 0.1
    
    PROB_EQUALS: float = 0.1
    PROB_LESS: float = 0.1
    PROB_GREATER: float = 0.1
    PROB_LESS_EQUALS: float = 0.1
    PROB_GREATER_EQUALS: float = 0.1
    PROB_SUM_FUNCTION: float = 0.1
    PROB_AVG_FUNCTION: float = 0.1
    PROB_LEN_FUNCTION: float = 0.1

    # Paso 4: Atributos
    RANDOM_ATTRIBUTES: bool = True
    MIN_ATTRIBUTES: int | None = 1
    MAX_ATTRIBUTES: int | None = 5
    ATTRIBUTES_LIST: list[Attribute] = field(default_factory=list)
    ATTRIBUTE_ATTACH_PROBS: list[float] = field(default_factory=list)
    ATTRIBUTE_IN_CONSTRAINTS: list[bool] = field(default_factory=list)


    def __post_init__(self):
        self.BOOLEAN_LEVEL = True  # siempre activado

        if self.TYPE_LEVEL:
            self.ARITHMETIC_LEVEL = True
            self.BOOLEAN_LEVEL = True
        elif self.ARITHMETIC_LEVEL:
            self.BOOLEAN_LEVEL = True

        if not self.ARITHMETIC_LEVEL:
            self.FEATURE_CARDINALITY = False
            self.AGGREGATE_FUNCTIONS = False

        if not self.TYPE_LEVEL:
            self.STRING_CONSTRAINTS = False

        # --- Validación de suma de probabilidades de relaciones ---
        total = (
            self.DIST_OPTIONAL +
            self.DIST_MANDATORY +
            self.DIST_ALTERNATIVE +
            self.DIST_OR +
            self.DIST_GROUP_CARDINALITY
        )
        if abs(total - 1.0) > 1e-6:
            raise ValueError(
                f"[ERROR] La suma de las probabilidades de relación no es 1.0 (actual: {total})"
            )
        
            # --- Validación de suma de probabilidades de constraints booleanas ---
        total_ctc = (
            self.PROB_AND +
            self.PROB_OR_CT +
            self.PROB_IMPLICATION +
            self.PROB_EQUIVALENCE
        )
        if abs(total_ctc - 1.0) > 1e-6:
            raise ValueError(
                f"[ERROR] La suma de PROB_AND, PROB_OR_CT, PROB_IMPLICATION y PROB_EQUIVALENCE debe ser 1.0 (actual: {total_ctc})"
            )


        # --- Validaciones de atributos ---
        if self.RANDOM_ATTRIBUTES:
            if self.MIN_ATTRIBUTES is None or self.MAX_ATTRIBUTES is None:
                raise ValueError("[ERROR] Debes definir MIN_ATTRIBUTES y MAX_ATTRIBUTES si RANDOM_ATTRIBUTES es True.")
        else:
            if self.MIN_ATTRIBUTES is not None or self.MAX_ATTRIBUTES is not None:
                raise ValueError("[ERROR] MIN_ATTRIBUTES y MAX_ATTRIBUTES deben ser None si RANDOM_ATTRIBUTES es False.")

            if len(self.ATTRIBUTES_LIST) != len(self.ATTRIBUTE_ATTACH_PROBS) or len(self.ATTRIBUTES_LIST) != len(self.ATTRIBUTE_IN_CONSTRAINTS):
                raise ValueError("[ERROR] Las listas ATTRIBUTES_LIST, ATTRIBUTE_ATTACH_PROBS y ATTRIBUTE_IN_CONSTRAINTS deben tener la misma longitud.")

            for i, p in enumerate(self.ATTRIBUTE_ATTACH_PROBS):
                if not (0.0 <= p <= 1.0):
                    raise ValueError(
                        f"[ERROR] La probabilidad de aparición del atributo en la posición {i} debe estar entre 0 y 1. Valor recibido: {p}"
                    )
