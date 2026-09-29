"""Engine-level unit tests: drive GenerateFeatureModel/FmgeneratorModel
directly and assert each generator parameter actually affects the output.

These tests are the backstop for "my level setting didn't do anything" bugs:
every level and its probability knobs are asserted here in isolation. The
end-to-end wizard tests in test_wizard_outputs.py check that the frontend
feeds the engine correctly.
"""

import re

import pytest

from flamapy.metamodels.fm_metamodel.models.feature_model import FeatureModel
from flamapy.metamodels.fm_metamodel.transformations.uvl_writer import (
    UVLWriter
)
from flamapy.metamodels.fm_generator.models import FmgeneratorModel
from flamapy.metamodels.fm_generator.operations import GenerateFeatureModel
from flamapy.metamodels.fm_metamodel.models.feature_model import (
    Feature,
    FeatureModel,
    FeatureType,
)
from flamapy.core.discover import DiscoverMetamodels



def _base_params(**overrides) -> FmgeneratorModel:
    """Minimal valid FmgeneratorModel built from the flat params dictionary
    currently produced by UVLHub. Overrides layer on top."""
    base = dict(
        NUM_MODELS=2,
        SEED=7,
        NAME_PREFIX="fm",
        ENSURE_SATISFIABLE=False,
        INCLUDE_FEATURE_COUNT_SUFFIX=False,
        INCLUDE_CONSTRAINT_COUNT_SUFFIX=False,
        ARITHMETIC_LEVEL=False,
        TYPE_LEVEL=False,
        GROUP_CARDINALITY=False,
        FEATURE_CARDINALITY=False,
        AGGREGATE_FUNCTIONS=False,
        STRING_CONSTRAINTS=False,
        MIN_FEATURES=6,
        MAX_FEATURES=10,
        MAX_TREE_DEPTH=3,
        FEATURE_DIST_BOOLEAN=1.0,
        FEATURE_DIST_INTEGER=0.0,
        FEATURE_DIST_REAL=0.0,
        FEATURE_DIST_STRING=0.0,
        DIST_OPTIONAL=0.3,
        DIST_MANDATORY=0.3,
        DIST_ALTERNATIVE=0.2,
        DIST_OR=0.2,
        DIST_GROUP_CARDINALITY=0.0,
        GROUP_CARDINALITY_MIN=1,
        GROUP_CARDINALITY_MAX=6,
        MIN_CONSTRAINTS=4,
        MAX_CONSTRAINTS=6,
        MIN_VARS_PER_CONSTRAINT=2,
        MAX_VARS_PER_CONSTRAINT=3,
        EXTRA_CONSTRAINT_REPRESENTATIVENESS=1,
        PROB_NOT=0.2,
        PROB_AND=0.4,
        PROB_OR_CT=0.2,
        PROB_IMPLICATION=0.2,
        PROB_EQUIVALENCE=0.2,
        PROB_SUM=0.4,
        PROB_SUBSTRACT=0.3,
        PROB_MULTIPLY=0.2,
        PROB_DIVIDE=0.1,
        PROB_EQUALS=0.2,
        PROB_LESS=0.2,
        PROB_GREATER=0.2,
        PROB_LESS_EQUALS=0.2,
        PROB_GREATER_EQUALS=0.2,
        PROB_SUM_FUNCTION=0.5,
        PROB_AVG_FUNCTION=0.5,
        PROB_LEN_FUNCTION=1.0,
        ATTR_DIST_BOOLEAN=1.0,
        ATTR_DIST_INTEGER=0.0,
        ATTR_DIST_REAL=0.0,
        ATTR_DIST_STRING=0.0,
        CTC_DIST_BOOLEAN=1.0,
        CTC_DIST_INTEGER=0.0,
        CTC_DIST_REAL=0.0,
        CTC_DIST_STRING=0.0,
        MIN_ATTRIBUTES=3,
        MAX_ATTRIBUTES=5,
    )
    base.update(overrides)
    return FmgeneratorModel.from_flat_dict(base)


def _prepend_uvl_includes(serialized_model: str, includes: list[str]) -> str:
    if not includes:
        return serialized_model

    include_block = "include\n" + \
        "\n".join(f"\t{inc}" for inc in includes) + "\n"
    return include_block + serialized_model


def _serialize_uvl(fm: FeatureModel) -> str:
    serialized_model = UVLWriter(None, fm).transform()
    return _prepend_uvl_includes(serialized_model, getattr(fm, "uvl_includes",
                                                           []))


def _run(model: FmgeneratorModel, n: int = 5) -> str:
    """Generate `n` models and return their concatenated UVL text."""
    model.num_models = n

    generator = GenerateFeatureModel()

    return "\n".join(_serialize_uvl(generator.execute(model, index=index)
                                    .get_result())
                     for index in range(n))


def _generate_feature_model(model: FmgeneratorModel, index: int = 0):
    operation = GenerateFeatureModel().execute(
        model,
        index=index,
    )
    return operation.get_result()


# ── NUM_MODELS + filename suffixes ───────────────────────────────────────


def test_num_models_respected():
    p = _base_params(NUM_MODELS=7)

    generator = GenerateFeatureModel()

    fms = [generator.execute(p, index=index).get_result()
           for index in range(p.num_models)]

    assert len(fms) == 7


def test_determinism_same_seed_same_output():
    a = _run(_base_params(SEED=123), n=3)
    b = _run(_base_params(SEED=123), n=3)
    assert a == b


def test_different_seed_different_output():
    a = _run(_base_params(SEED=1), n=3)
    b = _run(_base_params(SEED=999), n=3)
    assert a != b


# ── Features / tree ──────────────────────────────────────────────────────


def test_feature_count_in_range():
    """Every generated model must have MIN_FEATURES ≤ n ≤ MAX_FEATURES +1
    (the +1 covers the root)."""
    p = _base_params(MIN_FEATURES=5, MAX_FEATURES=8)
    text = _run(p, n=5)
    # Count `F\d+` tokens but group by model
    models = [m for m in text.split("features\n") if m.strip()]
    for m in models:
        feats = set(re.findall(r"F\d+\b", m))
        assert 5 <= len(
            feats) <= 9, f"feature count out of range: {len(feats)}"


def test_max_tree_depth_respected():
    """No child feature should live deeper than MAX_TREE_DEPTH levels below
    the root. Features are indented with tabs in UVL; each level adds 2 tabs
    (one for the relation keyword, one for the child). Root sits at 1 tab,
    so max depth D means the deepest feature is at 1 + 2*D tabs."""
    p = _base_params(MAX_TREE_DEPTH=3, MIN_FEATURES=6, MAX_FEATURES=10)
    text = _run(p, n=3)
    feat_lines = [ln for ln in text.splitlines() if re.match(r"\t+F\d+\b", ln)]
    max_indent = max(len(ln) - len(ln.lstrip("\t")) for ln in feat_lines)
    assert max_indent <= 1 + 2 * \
        3, f"deepest feature at {max_indent} tabs exceeds cap"


def test_group_cardinality_off_produces_no_group_relations():
    p = _base_params(
        GROUP_CARDINALITY=False,
        DIST_OPTIONAL=0.25,
        DIST_MANDATORY=0.25,
        DIST_ALTERNATIVE=0.25,
        DIST_OR=0.25,
        DIST_GROUP_CARDINALITY=0.0,
    )
    text = _run(p, n=5)
    # Group-cardinality relations serialise as "[n]" or "[n..m]" markers as
    # standalone relation indicator (not cardinality [n..m] which attaches to
    # a feature).
    assert "group_cardinality" not in text.lower()


def test_group_cardinality_on_with_weight_produces_group_groups():
    p = _base_params(
        GROUP_CARDINALITY=True,
        DIST_OPTIONAL=0.1,
        DIST_MANDATORY=0.1,
        DIST_ALTERNATIVE=0.1,
        DIST_OR=0.1,
        DIST_GROUP_CARDINALITY=0.6,
        MIN_FEATURES=8,
        MAX_FEATURES=12,
    )
    text = _run(p, n=5)
    # UVLWriter writes bare "[n..m]" for cardinality-group relations.
    # Feature cardinality is "cardinality [n..m]" with the keyword, so we
    # search for the bare form.
    lines = text.splitlines()
    bare_card = [ln for ln in lines if re.match(
        r"^\s*\[\d+(\.\.\d+)?\]\s*$", ln)]
    assert len(bare_card) > 0, "no group-cardinality relations emitted"


def test_feature_cardinality_off_produces_none():
    p = _base_params(
        ARITHMETIC_LEVEL=True,
        FEATURE_CARDINALITY=False,
        ATTR_DIST_BOOLEAN=1.0,
        ATTR_DIST_INTEGER=0.0,
        ATTR_DIST_REAL=0.0,
        CTC_DIST_BOOLEAN=1.0,
        CTC_DIST_INTEGER=0.0,
        CTC_DIST_REAL=0.0,
    )
    text = _run(p, n=5)
    assert "cardinality [" not in text


def test_feature_cardinality_on_produces_some():
    p = _base_params(
        ARITHMETIC_LEVEL=True,
        FEATURE_CARDINALITY=True,
        PROB_FEATURE_CARDINALITY=1.0,
        MIN_FEATURE_CARDINALITY=[2],
        MAX_FEATURE_CARDINALITY=[5],
        ATTR_DIST_BOOLEAN=1.0,
        ATTR_DIST_INTEGER=0.0,
        ATTR_DIST_REAL=0.0,
        CTC_DIST_BOOLEAN=1.0,
        CTC_DIST_INTEGER=0.0,
        CTC_DIST_REAL=0.0,
    )
    text = _run(p, n=3)
    assert "cardinality [" in text


# ── Attributes / type distribution ───────────────────────────────────────


def test_random_attributes_respects_count_range():
    p = _base_params(MIN_ATTRIBUTES=3, MAX_ATTRIBUTES=3)
    text = _run(p, n=4)
    for model in text.split("features\n")[1:]:
        names = set(re.findall(r"\bAttr\d+", model))
        assert len(names) == 3, f"expected 3 attrs, got {len(names)}"


def test_dist_boolean_only_produces_only_boolean_attrs():
    p = _base_params(
        ATTR_DIST_BOOLEAN=1.0,
        ATTR_DIST_INTEGER=0.0,
        ATTR_DIST_REAL=0.0,
        ATTR_DIST_STRING=0.0,
        MIN_ATTRIBUTES=3,
        MAX_ATTRIBUTES=3,
    )
    text = _run(p, n=3)
    # Boolean attrs serialise as "{Name true}" or "{Name false}".
    attrs = re.findall(r"\{Attr\d+\s+(\S+?)(?:,|\})", text)
    assert attrs, "no attributes found"
    assert all(a in ("true", "false")
               for a in attrs), f"non-boolean attrs: {attrs}"


def test_dist_integer_only_produces_integer_attrs():
    p = _base_params(
        ARITHMETIC_LEVEL=True,
        ATTR_DIST_BOOLEAN=0.0,
        ATTR_DIST_INTEGER=1.0,
        ATTR_DIST_REAL=0.0,
        ATTR_DIST_STRING=0.0,
        MIN_ATTRIBUTES=3,
        MAX_ATTRIBUTES=3,
    )
    text = _run(p, n=3)
    attrs = re.findall(r"\{Attr\d+\s+([^,}]+)", text)
    # Integers emit as bare ints like "57", not quoted, not booleans.
    for v in attrs:
        v = v.strip()
        assert re.match(r"^-?\d+$", v), f"expected integer, got {v!r}"


def test_dist_string_only_respects_type_level():
    p = _base_params(
        TYPE_LEVEL=True,
        ATTR_DIST_BOOLEAN=0.0,
        ATTR_DIST_INTEGER=0.0,
        ATTR_DIST_REAL=0.0,
        ATTR_DIST_STRING=1.0,
        MIN_ATTRIBUTES=3,
        MAX_ATTRIBUTES=3,
    )
    text = _run(p, n=3)
    # Strings emit quoted: {Attr0 'low'}
    assert re.search(r"\{Attr\d+\s+'[^']+'", text)


def test_numeric_attrs_do_not_appear_in_constraints_when_arithmetic_off():
    """Numeric attributes may exist with Arithmetic level disabled, but they
    must not be used in constraints."""
    p = _base_params(
        ARITHMETIC_LEVEL=False,
        TYPE_LEVEL=False,
        ATTR_DIST_BOOLEAN=0.0,
        ATTR_DIST_INTEGER=1.0,
        ATTR_DIST_REAL=0.0,
        ATTR_DIST_STRING=0.0,
        CTC_DIST_BOOLEAN=1.0,
        CTC_DIST_INTEGER=0.0,
        CTC_DIST_REAL=0.0,
        CTC_DIST_STRING=0.0,
        MIN_ATTRIBUTES=3,
        MAX_ATTRIBUTES=3,
        MIN_CONSTRAINTS=6,
        MAX_CONSTRAINTS=6,
    )

    text = _run(p, n=3)

    attrs = re.findall(r"\{Attr\d+\s+([^,}]+)", text)
    assert attrs, "expected numeric attributes to be generated"

    for line in _iter_constraint_lines(text):
        assert ".Attr" not in line, (
            f"attribute leaked into boolean-only constraint: {line}"
        )


# ── Constraints / levels ─────────────────────────────────────────────────


def test_boolean_only_level_has_no_arith_no_strings():
    p = _base_params(
        ARITHMETIC_LEVEL=False,
        TYPE_LEVEL=False,
        MIN_CONSTRAINTS=8,
        MAX_CONSTRAINTS=10,
    )
    text = _run(p, n=3)
    # No aggregate keywords, no len(), no arithmetic operators in constraints.
    ctc_section = re.split(r"constraints\n", text)
    body = "\n".join(ctc_section[1:]) if len(ctc_section) > 1 else ""
    assert "sum(" not in body
    assert "avg(" not in body
    assert "len(" not in body
    # Arithmetic ops only inside constraints — standalone `+ - * /` won't
    # appear in pure Boolean constraints.
    arith_in_ctc = re.search(r"[+\-*/]", body)
    # Actually Boolean constraints don't contain + - * /; negation is "!" and
    # implies is "=>".
    assert arith_in_ctc is None or "!=" in body, (
        "unexpected arithmetic in boolean-only constraints"
    )
    "boolean-only constraints"


def test_arithmetic_level_produces_arith_constraints():
    p = _base_params(
        ARITHMETIC_LEVEL=True,
        ATTR_DIST_BOOLEAN=0.0,
        ATTR_DIST_INTEGER=1.0,
        ATTR_DIST_REAL=0.0,
        ATTR_DIST_STRING=0.0,
        # Force arithmetic CTCs: weight boolean low, integer high.
        CTC_DIST_BOOLEAN=0.0,
        CTC_DIST_INTEGER=1.0,
        CTC_DIST_REAL=0.0,
        CTC_DIST_STRING=0.0,
        MIN_CONSTRAINTS=10,
        MAX_CONSTRAINTS=10,
        MIN_ATTRIBUTES=3,
        MAX_ATTRIBUTES=4,
    )
    text = _run(p, n=5)
    body = "\n".join(_iter_constraint_lines(text))
    # Expect at least one arithmetic operator in a constraint.
    assert re.search(
        r"\s[+\-*/]\s", body), f"no arithmetic constraints emitted:\n{body}"


def test_aggregate_functions_produce_sum_avg():
    p = _base_params(
        ARITHMETIC_LEVEL=True,
        AGGREGATE_FUNCTIONS=True,
        ATTR_DIST_BOOLEAN=0.0,
        ATTR_DIST_INTEGER=1.0,
        ATTR_DIST_REAL=0.0,
        ATTR_DIST_STRING=0.0,
        CTC_DIST_BOOLEAN=0.0,
        CTC_DIST_INTEGER=1.0,
        CTC_DIST_REAL=0.0,
        CTC_DIST_STRING=0.0,
        PROB_SUM=0.0,
        PROB_SUBSTRACT=0.0,
        PROB_MULTIPLY=0.0,
        PROB_DIVIDE=0.0,
        PROB_SUM_FUNCTION=0.5,
        PROB_AVG_FUNCTION=0.5,
        MIN_CONSTRAINTS=15,
        MAX_CONSTRAINTS=15,
        MIN_ATTRIBUTES=3,
        MAX_ATTRIBUTES=4,
    )
    text = _run(p, n=5)
    body = "\n".join(_iter_constraint_lines(text))
    assert "sum(" in body or "avg(" in body, (
        f"no aggregate constraints emitted:\n{body}"
    )
    "emitted:\n{body}"


def test_string_level_produces_len_constraints():
    p = _base_params(
        TYPE_LEVEL=True,
        STRING_CONSTRAINTS=True,
        ATTR_DIST_BOOLEAN=0.0,
        ATTR_DIST_INTEGER=0.0,
        ATTR_DIST_REAL=0.0,
        ATTR_DIST_STRING=1.0,
        CTC_DIST_BOOLEAN=0.0,
        CTC_DIST_INTEGER=0.0,
        CTC_DIST_REAL=0.0,
        CTC_DIST_STRING=1.0,
        PROB_LEN_FUNCTION=1.0,
        MIN_CONSTRAINTS=10,
        MAX_CONSTRAINTS=10,
        MIN_ATTRIBUTES=3,
        MAX_ATTRIBUTES=4,
    )
    text = _run(p, n=5)
    body = "\n".join(_iter_constraint_lines(text))
    assert "len(" in body, f"no string (len) constraints emitted:\n{body}"


def test_len_constraints_mix_with_arithmetic_but_not_with_aggregates():
    """
    len() expressions can participate in arithmetic operations, but they
    must never be placed inside aggregate functions.
    """
    p = _base_params(
        TYPE_LEVEL=True,
        STRING_CONSTRAINTS=True,
        ARITHMETIC_LEVEL=True,
        AGGREGATE_FUNCTIONS=True,
        ATTR_DIST_BOOLEAN=0.0,
        ATTR_DIST_INTEGER=0.5,
        ATTR_DIST_REAL=0.0,
        ATTR_DIST_STRING=0.5,
        CTC_DIST_BOOLEAN=0.0,
        CTC_DIST_INTEGER=1.0,
        CTC_DIST_REAL=0.0,
        CTC_DIST_STRING=0.0,
        PROB_LEN_FUNCTION=1.0,
        # Force arithmetic generation
        PROB_SUM=0.5,
        PROB_SUBSTRACT=0.0,
        PROB_MULTIPLY=0.0,
        PROB_DIVIDE=0.0,
        # Enable aggregates but they must not consume len()
        PROB_SUM_FUNCTION=0.25,
        PROB_AVG_FUNCTION=0.25,
        MIN_CONSTRAINTS=20,
        MAX_CONSTRAINTS=20,
        MIN_ATTRIBUTES=4,
        MAX_ATTRIBUTES=4,
    )

    text = _run(p, n=10)
    body = "\n".join(_iter_constraint_lines(text))

    assert "len(" in body, "no len() constraints generated"

    # len() must appear inside arithmetic expressions
    arithmetic_len = re.search(
        r"(len\([^)]+\)\s*[+\-*/]\s*\w+)" r"|(\w+\s*[+\-*/]\s*len\([^)]+\))",
        body,
    )

    assert arithmetic_len, (
        "len() never appeared combined with arithmetic operands:\n"
        f"{body}"
    )

    # Aggregates cannot contain len()
    assert "sum(len(" not in body
    assert "avg(len(" not in body


def _iter_constraint_lines(text: str):
    """Yield each constraint line across all models in `text`. Each model
    block is ``features\\n...\\nconstraints\\n<lines>``; we can't just
    split on 'constraints\\n' once because the concat loops through N
    models."""
    in_ctc = False
    for line in text.splitlines():
        if line == "features":
            in_ctc = False
            continue
        if line == "constraints":
            in_ctc = True
            continue
        if in_ctc and line.strip():
            yield line.strip()


def test_min_vars_per_constraint_respected():
    """With MIN=MAX=4, every Boolean constraint has exactly 4 leaves."""
    p = _base_params(
        MIN_VARS_PER_CONSTRAINT=4,
        MAX_VARS_PER_CONSTRAINT=4,
        PROB_NOT=0.0,
        EXTRA_CONSTRAINT_REPRESENTATIVENESS=1,
        MIN_CONSTRAINTS=6,
        MAX_CONSTRAINTS=6,
        MIN_FEATURES=10,
        MAX_FEATURES=15,
        MIN_ATTRIBUTES=0,
        MAX_ATTRIBUTES=0,  # no attributes → purely Boolean ctcs
    )
    text = _run(p, n=3)
    for line in _iter_constraint_lines(text):
        refs = re.findall(r"\bF\d+\b", line)
        assert len(refs) == 4, (
            f"expected 4 vars in constraint, got {len(refs)}: {line}"
        )
        assert len(set(refs)) == 4

def test_prob_not_zero_produces_no_negations():
    p = _base_params(
        PROB_NOT=0.0,
        MIN_CONSTRAINTS=8,
        MAX_CONSTRAINTS=8,
    )
    text = _run(p, n=5)
    ctc_body = text.split("constraints\n", 1)[
        1] if "constraints\n" in text else ""
    # '!' only appears in negation in UVL syntax. The writer uses "! ".
    assert "! " not in ctc_body, "unexpected NOT in constraints"


def test_min_max_constraints_respected():
    p = _base_params(MIN_CONSTRAINTS=3, MAX_CONSTRAINTS=3)
    for _ in range(5):
        text = _run(p, n=1)
        ctc_body = text.split("constraints\n", 1)[
            1] if "constraints\n" in text else ""
        lines = [ln for ln in ctc_body.splitlines() if ln.strip()]
        assert len(lines) == 3


# ── ENSURE_SATISFIABLE ───────────────────────────────────────────────────


def test_ensure_satisfiable_runs_without_crashing():
    """Smoke test: satisfiable generation inputs must not raise."""
    p = _base_params(ENSURE_SATISFIABLE=True, NUM_MODELS=2)
    generator = GenerateFeatureModel()

    fms = [generator.execute(p, index=index).get_result()
           for index in range(p.num_models)]

    assert len(fms) == 2


# ── Manual attribute mode ────────────────────────────────────────────────


def test_manual_mode_uses_attribute_in_constraints_flag():
    """Attributes with use_in_constraints=False must not appear in any
    constraint expression (across every generated model)."""
    attr = {
        "name": "SecretSize",
        "type": "boolean",
        "value": [True, False],
        "attach_probability": 1.0,
        "use_in_constraints": False,
    }
    p = _base_params(
        RANDOM_ATTRIBUTES=False,
        MIN_ATTRIBUTES=None,
        MAX_ATTRIBUTES=None,
        ATTRIBUTES_LIST=[attr],
        ATTRIBUTE_ATTACH_PROBS=[1.0],
        ATTRIBUTE_IN_CONSTRAINTS=[False],
        MIN_CONSTRAINTS=5,
        MAX_CONSTRAINTS=5,
    )
    text = _run(p, n=2)
    for line in _iter_constraint_lines(text):
        assert "SecretSize" not in line, f"attr leaked into constraint: {line}"


def test_constant_seed_and_index_determinism():
    """GenerateFeatureModel.execute must be deterministic on (seed, index)."""
    p = _base_params(SEED=42)

    a = (
        GenerateFeatureModel()
        .execute(
            p,
            index=0,
        )
        .get_result()
    )

    b = (
        GenerateFeatureModel()
        .execute(
            p,
            index=0,
        )
        .get_result()
    )

    assert [f.name for f in a.get_features()] == [
        f.name for f in b.get_features()]

    assert len(a.ctcs) == len(b.ctcs)


@pytest.mark.parametrize(
    ("overrides", "expected"),
    [
        ({}, []),
        (
            {
                "GROUP_CARDINALITY": True,
                "DIST_OPTIONAL": 0.2,
                "DIST_MANDATORY": 0.2,
                "DIST_ALTERNATIVE": 0.2,
                "DIST_OR": 0.2,
                "DIST_GROUP_CARDINALITY": 0.2,
            },
            ["Boolean.group-cardinality"],
        ),
        (
            {
                "ARITHMETIC_LEVEL": True,
                "AGGREGATE_FUNCTIONS": True,
                "PROB_SUM": 0.0,
                "PROB_SUBSTRACT": 0.0,
                "PROB_MULTIPLY": 0.0,
                "PROB_DIVIDE": 0.0,
                "PROB_SUM_FUNCTION": 0.5,
                "PROB_AVG_FUNCTION": 0.5,
            },
            ["Arithmetic.aggregate-function"],
        ),
        (
            {
                "ARITHMETIC_LEVEL": True,
                "FEATURE_CARDINALITY": True,
            },
            ["Arithmetic.feature-cardinality"],
        ),
        (
            {
                "ARITHMETIC_LEVEL": True,
                "AGGREGATE_FUNCTIONS": True,
                "FEATURE_CARDINALITY": True,
                "PROB_SUM": 0.0,
                "PROB_SUBSTRACT": 0.0,
                "PROB_MULTIPLY": 0.0,
                "PROB_DIVIDE": 0.0,
                "PROB_SUM_FUNCTION": 0.5,
                "PROB_AVG_FUNCTION": 0.5,
            },
            ["Arithmetic.*"],
        ),
        (
            {
                "TYPE_LEVEL": True,
                "STRING_CONSTRAINTS": True,
            },
            ["Type.string-constraints"],
        ),
    ],
)
def test_generated_model_declares_correct_uvl_includes(overrides, expected):
    model = _base_params(**overrides)
    feature_model = _generate_feature_model(model)

    assert feature_model.uvl_includes == expected


@pytest.mark.parametrize(
    ("selected_type", "expected_type"),
    [
        ("FEATURE_DIST_INTEGER", FeatureType.INTEGER),
        ("FEATURE_DIST_REAL", FeatureType.REAL),
        ("FEATURE_DIST_STRING", FeatureType.STRING),
    ],
)
def test_feature_distribution_controls_feature_type(
    selected_type,
    expected_type,
):
    distributions = {
        "FEATURE_DIST_BOOLEAN": 0.0,
        "FEATURE_DIST_INTEGER": 0.0,
        "FEATURE_DIST_REAL": 0.0,
        "FEATURE_DIST_STRING": 0.0,
    }
    distributions[selected_type] = 1.0

    model = _base_params(
        TYPE_LEVEL=True,
        ARITHMETIC_LEVEL=True,
        **distributions,
    )

    feature_model = _generate_feature_model(model)

    generated_features = [
        feature
        for feature in feature_model.get_features()
        if feature.name != "F0"
    ]

    assert generated_features
    assert all(
        feature.feature_type == expected_type
        for feature in generated_features
    )


def test_manual_mode_generates_all_supported_attribute_types():
    attributes = [
        {
            "name": "Enabled",
            "type": "boolean",
            "value": "true",
            "attach_probability": 1.0,
            "use_in_constraints": True,
        },
        {
            "name": "Count",
            "type": "integer",
            "min_value": 1,
            "max_value": 5,
            "attach_probability": 1.0,
            "use_in_constraints": True,
        },
        {
            "name": "Price",
            "type": "real",
            "min_value": 0.5,
            "max_value": 2.5,
            "attach_probability": 1.0,
            "use_in_constraints": True,
        },
        {
            "name": "Label",
            "type": "string",
            "min_value": 2,
            "max_value": 5,
            "attach_probability": 1.0,
            "use_in_constraints": True,
        },
    ]

    model = _base_params(
        RANDOM_ATTRIBUTES=False,
        MIN_ATTRIBUTES=None,
        MAX_ATTRIBUTES=None,
        ATTRIBUTES_LIST=attributes,
        ATTRIBUTE_ATTACH_PROBS=[1.0, 1.0, 1.0, 1.0],
        ATTRIBUTE_IN_CONSTRAINTS=[True, True, True, True],
        ARITHMETIC_LEVEL=True,
        TYPE_LEVEL=True,
        STRING_CONSTRAINTS=True,
    )

    feature_model = _generate_feature_model(model)

    generated_attributes = {
        attribute.name: attribute
        for feature in feature_model.get_features()
        for attribute in getattr(feature, "attributes", [])
    }

    assert {
        "Enabled",
        "Count",
        "Price",
        "Label",
    } <= generated_attributes.keys()

    assert generated_attributes["Enabled"].attribute_type == "boolean"
    assert generated_attributes["Count"].attribute_type == "integer"
    assert generated_attributes["Price"].attribute_type == "real"
    assert generated_attributes["Label"].attribute_type == "string"


def test_real_attribute_distribution_generates_real_attributes():
    model = _base_params(
        ARITHMETIC_LEVEL=True,
        ATTR_DIST_BOOLEAN=0.0,
        ATTR_DIST_INTEGER=0.0,
        ATTR_DIST_REAL=1.0,
        ATTR_DIST_STRING=0.0,
        MIN_ATTRIBUTES=3,
        MAX_ATTRIBUTES=3,
    )

    feature_model = _generate_feature_model(model)

    attributes = [
        attribute
        for feature in feature_model.get_features()
        for attribute in getattr(feature, "attributes", [])
    ]

    assert len(attributes) == 3
    assert all(attribute.attribute_type == "real" for attribute in attributes)


def test_zero_len_probability_generates_string_equality_constraints():
    model = _base_params(
        TYPE_LEVEL=True,
        STRING_CONSTRAINTS=True,
        FEATURE_DIST_BOOLEAN=0.0,
        FEATURE_DIST_INTEGER=0.0,
        FEATURE_DIST_REAL=0.0,
        FEATURE_DIST_STRING=1.0,
        ATTR_DIST_BOOLEAN=0.0,
        ATTR_DIST_INTEGER=0.0,
        ATTR_DIST_REAL=0.0,
        ATTR_DIST_STRING=1.0,
        CTC_DIST_BOOLEAN=0.0,
        CTC_DIST_INTEGER=0.0,
        CTC_DIST_REAL=0.0,
        CTC_DIST_STRING=1.0,
        PROB_LEN_FUNCTION=0.0,
        MIN_CONSTRAINTS=8,
        MAX_CONSTRAINTS=8,
    )

    body = "\n".join(
        _iter_constraint_lines(_run(model, n=3))
    )

    assert "len(" not in body
    assert "==" in body


def test_relation_kinds_create_expected_cardinalities():
    generator = GenerateFeatureModel()
    generator.model = _base_params(GROUP_CARDINALITY=True)

    parent = Feature("Parent")
    children = [
        Feature("Child1"),
        Feature("Child2"),
        Feature("Child3"),
    ]

    mandatory = generator._create_relation(parent, children, "mand")
    assert len(mandatory) == 3
    assert all(
        relation.card_min == 1 and relation.card_max == 1
        for relation in mandatory
    )

    optional = generator._create_relation(parent, children, "opt")
    assert len(optional) == 3
    assert all(
        relation.card_min == 0 and relation.card_max == 1
        for relation in optional
    )

    alternative = generator._create_relation(parent, children, "alt")
    assert len(alternative) == 1
    assert (
        alternative[0].card_min,
        alternative[0].card_max,
    ) == (1, 1)

    or_relation = generator._create_relation(parent, children, "or")
    assert len(or_relation) == 1
    assert (
        or_relation[0].card_min,
        or_relation[0].card_max,
    ) == (1, 3)

    group = generator._create_relation(parent, children, "group")
    assert len(group) == 1
    assert 1 <= group[0].card_min <= group[0].card_max <= 3


def test_generate_feature_model_is_discoverable_by_flamapy():
    """Flamapy must discover and execute the plugin operation."""
    discovered_operations = DiscoverMetamodels().get_operations()

    if isinstance(discovered_operations, dict):
        discovered_operations = discovered_operations.values()

    generate_operation = next(
        (
            operation
            for operation in discovered_operations
            if (
                operation.__name__
                if isinstance(operation, type)
                else operation.__class__.__name__
            )
            == "GenerateFeatureModel"
        ),
        None,
    )

    assert generate_operation is not None

    operation = (
        generate_operation()
        if isinstance(generate_operation, type)
        else generate_operation
    )

    result = operation.execute(_base_params()).get_result()

    assert isinstance(result, FeatureModel)
    assert result.root is not None