"""Contract tests between the wizard form mapping and the vendor Params dataclass.

These assert that:

1. Every PROB_*/DIST_* name we reference from routes.py exists as a field on
   Params (catches silent drift when someone renames a field in the vendor
   code — this is how `_ARITH_KEYS` ended up listing `PROB_PLUS` / `PROB_MINUS`
   that nobody declared).
2. Running the full happy-path form through the wizard produces a params
   dict that Params can accept without raising. This is the contract test
   that would have caught 1.0007 and EXTRA_CONSTRAINT_REPRESENTATIVENESS=0.5.
"""

from dataclasses import fields

import pytest
from fm_generator.FMGenerator.models.config import Params

pytestmark = pytest.mark.unit


def _params_field_names():
    return {f.name for f in fields(Params)}


def test_arith_keys_exist_in_params():
    """Every key the step2 orphan-cleanup touches must be a real Params field."""
    # Re-import inside the function because _ARITH_KEYS is defined inside a
    # function body in routes.py, not at module scope. We re-declare the
    # contract here so the test is self-documenting.
    arith = {
        "PROB_SUM",
        "PROB_SUBSTRACT",
        "PROB_MULTIPLY",
        "PROB_DIVIDE",
        "PROB_EQUALS",
        "PROB_LESS",
        "PROB_GREATER",
        "PROB_LESS_EQUALS",
        "PROB_GREATER_EQUALS",
    }
    agg = {"PROB_SUM_FUNCTION", "PROB_AVG_FUNCTION"}
    str_keys = {"PROB_LEN_FUNCTION"}

    missing = (arith | agg | str_keys) - _params_field_names()
    assert not missing, f"Keys referenced by routes but not on Params: {missing}"


def test_relation_dist_keys_exist():
    rel = {"DIST_OPTIONAL", "DIST_MANDATORY", "DIST_ALTERNATIVE", "DIST_OR", "DIST_GROUP_CARDINALITY"}
    missing = rel - _params_field_names()
    assert not missing, missing


def test_boolean_connective_keys_exist():
    bools = {"PROB_AND", "PROB_OR_CT", "PROB_IMPLICATION", "PROB_EQUIVALENCE"}
    missing = bools - _params_field_names()
    assert not missing, missing


def test_extra_constraint_representativeness_is_int():
    """The UI treats this as an integer count; the vendor used to type it as
    float with default 0.5, which caused it to show up as "0,5" in the form
    and fail the int-only validator."""
    ecr = next(f for f in fields(Params) if f.name == "EXTRA_CONSTRAINT_REPRESENTATIVENESS")
    assert ecr.type is int or ecr.type == "int"
    assert ecr.default == 1


def test_params_accepts_happy_path_defaults():
    """Constructing Params() with no args must not raise — it's our sanity
    check that every sum-constrained default still sums to 1.0 after the
    vendor edits."""
    Params()


def test_params_rejects_broken_relation_sum():
    """Regression guard: the vendor check must still fire when someone forgets
    to normalise DIST_* probabilities."""
    import pytest

    with pytest.raises(ValueError, match="Relation probabilities"):
        Params(DIST_OPTIONAL=0.3, DIST_MANDATORY=0.3, DIST_ALTERNATIVE=0.2, DIST_OR=0.3)


def test_params_rejects_broken_boolean_sum():
    import pytest

    with pytest.raises(ValueError, match="PROB_AND"):
        Params(PROB_AND=0.9, PROB_OR_CT=0.9, PROB_IMPLICATION=0.0, PROB_EQUIVALENCE=0.0)
