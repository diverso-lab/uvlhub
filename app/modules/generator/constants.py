STEP2_CHECKBOX_FIELDS = [
    "boolean_level",
    "arithmetic_level",
    "type_level",
    "feature_cardinality",
    "aggregate_functions",
    "string_constraints",
    "group_cardinality",
]

STEP5_CHECKBOX_FIELDS = ["random_attributes"]

STEP6_CHECKBOX_FIELDS = [
    "ensure_satisfiable",
    "feature_count_suffix",
    "constraint_count_suffix",
]

RELATION_DIST_KEYS = [
    "DIST_OPTIONAL",
    "DIST_MANDATORY",
    "DIST_ALTERNATIVE",
    "DIST_OR",
    "DIST_GROUP_CARDINALITY",
]

BOOLEAN_CONNECTIVE_KEYS = [
    "PROB_AND",
    "PROB_OR_CT",
    "PROB_IMPLICATION",
    "PROB_EQUIVALENCE",
]

ARITHMETIC_PROB_KEYS = [
    "PROB_SUM",
    "PROB_SUBSTRACT",
    "PROB_MULTIPLY",
    "PROB_DIVIDE",
    "PROB_SUM_FUNCTION",
    "PROB_AVG_FUNCTION",
    "PROB_EQUALS",
    "PROB_LESS",
    "PROB_GREATER",
    "PROB_LESS_EQUALS",
    "PROB_GREATER_EQUALS",
]

CTC_DIST_KEYS = [
    "CTC_DIST_BOOLEAN",
    "CTC_DIST_INTEGER",
    "CTC_DIST_REAL",
    "CTC_DIST_STRING",
]

ATTRIBUTE_DIST_KEYS = [
    "DIST_BOOLEAN",
    "DIST_INTEGER",
    "DIST_REAL",
    "DIST_STRING",
]

STEP4_UI_DEFAULTS = {
    "prob_plus": 0.7,
    "prob_minus": 0.2,
    "prob_times": 0.1,
    "prob_div": 0.0,
    "prob_sum": 0.0,
    "prob_avg": 0.0,
    "prob_eq": 0.1,
    "prob_lt": 0.2,
    "prob_gt": 0.7,
    "prob_leq": 0.0,
    "prob_geq": 0.0,
    "prob_len": 0.7,
}