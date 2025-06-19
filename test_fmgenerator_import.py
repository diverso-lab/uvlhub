from flamapy.metamodels.fm_metamodel.transformations.uvl_writer import UVLWriter
from fm_generator.src.fm_generator.FMGenerator.models.config import Params
from fm_generator.src.fm_generator.FMGenerator.models.models import FmgeneratorModel
from flamapy.metamodels.fm_metamodel.models.feature_model import Attribute, Domain, Range
import random

if __name__ == "__main__":

    # Atributo booleano
    attr1 = Attribute(
        name="Enabled",
        domain=Domain(ranges=None, elements=[True, False]),
        default_value=True
    )

    # Atributo entero
    attr2 = Attribute(
        name="Capacity",
        domain=Domain(ranges=[Range(10, 50)], elements=None),
        default_value=30
    )

    # Atributo string
    attr3 = Attribute(
        name="Priority",
        domain=Domain(ranges=None, elements=["low", "medium", "high"]),
        default_value="medium"
    )

    # Lista de atributos y configuraciones asociadas
    attributes = [attr1, attr2, attr3]
    attach_probs = [0.1, 0.1, 0.1]  # Probabilidad de que cada uno aparezca en una feature
    usable_in_ctcs = [True, True, False]  # Si se puede usar en constraints


    params = Params(
        NUM_MODELS=5,
        SEED=1090093,
        # ENSURE_SATISFIABLE=True,
        NAME_PREFIX="fm",
        # INCLUDE_FEATURE_COUNT_SUFFIX=True,
        # INCLUDE_CONSTRAINT_COUNT_SUFFIX=False,

        BOOLEAN_LEVEL=True,
        ARITHMETIC_LEVEL=True,
        TYPE_LEVEL=True,
        GROUP_CARDINALITY=True,
        FEATURE_CARDINALITY=True,
        AGGREGATE_FUNCTIONS=True,
        STRING_CONSTRAINTS=True,

        MIN_FEATURES=10,
        MAX_FEATURES=16,
        DIST_BOOLEAN=0.4,
        DIST_INTEGER=0.2,
        DIST_REAL=0.2,
        DIST_STRING=0.2,

        MIN_FEATURE_CARDINALITY=[2],
        MAX_FEATURE_CARDINALITY=[4, 5],
        PROB_FEATURE_CARDINALITY = 0.4,

        MAX_TREE_DEPTH=4,
        DIST_OPTIONAL=0.8,
        DIST_MANDATORY=0.05,
        DIST_ALTERNATIVE=0.05,
        DIST_OR=0.05,
        DIST_GROUP_CARDINALITY=0.05,
        GROUP_CARDINALITY_MIN=3,
        GROUP_CARDINALITY_MAX=7,

        MIN_CONSTRAINTS=5,
        MAX_CONSTRAINTS=10,
        EXTRA_CONSTRAINT_REPRESENTATIVENESS=0.5,
        MIN_VARS_PER_CONSTRAINT=1,
        MAX_VARS_PER_CONSTRAINT=3,

        PROB_NOT=0.3,
        PROB_AND=0.1,
        PROB_OR_CT=0.1,
        PROB_IMPLICATION=0.1,
        PROB_EQUIVALENCE=0.7,

        PROB_SUM=0.1,
        PROB_SUBSTRACT=0.1,
        PROB_MULTIPLY=0.1,
        PROB_DIVIDE=0.1,
        PROB_EQUALS=0.1,
        PROB_LESS=0.1,
        PROB_GREATER=0.1,
        PROB_LESS_EQUALS=0.1,
        PROB_GREATER_EQUALS=0.1,
        PROB_SUM_FUNCTION=0.1,
        PROB_AVG_FUNCTION=0.1,
        PROB_LEN_FUNCTION=0.1,


        RANDOM_ATTRIBUTES=False,
        MIN_ATTRIBUTES=None,
        MAX_ATTRIBUTES=None,
        ATTRIBUTES_LIST=attributes,
        ATTRIBUTE_ATTACH_PROBS=attach_probs,
        ATTRIBUTE_IN_CONSTRAINTS=usable_in_ctcs,
    )

    generator = FmgeneratorModel(params)
    models = generator.generate_models()
