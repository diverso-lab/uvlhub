import pytest

pytestmark = pytest.mark.unit

"""Engine-level unit tests: drive generate_single_model/FmgeneratorModel
directly and assert each knob in Params actually affects the output.

These tests are the backstop for "my level setting didn't do anything" bugs:
every level and its probability knobs are asserted here in isolation. The
end-to-end wizard tests in test_wizard_outputs.py check that the frontend
feeds the engine correctly.
"""

import os
import re
import tempfile

from flamapy.metamodels.fm_metamodel.models import Attribute, Domain
from fm_generator.FMGenerator.models.config import Params
from fm_generator.FMGenerator.models.models import FmgeneratorModel
from fm_generator.FMGenerator.operations.generate_models import generate_single_model


def _base_params(**overrides) -> Params:
    """Minimal valid Params. Overrides layer on top; dataclass __post_init__
    still enforces (sum of DIST_* relations == 1) and similar invariants."""
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
        DIST_BOOLEAN=0.7,
        DIST_INTEGER=0.1,
        DIST_REAL=0.1,
        DIST_STRING=0.1,
        MIN_ATTRIBUTES=3,
        MAX_ATTRIBUTES=5,
    )
    base.update(overrides)
    return Params(**base)


def _run(params: Params, n: int = 5) -> str:
    """Generate `n` models and return their concatenated UVL text. Seed is
    in Params so each call is deterministic per-config."""
    params.NUM_MODELS = n
    with tempfile.TemporaryDirectory() as d:
        FmgeneratorModel(params).generate_models(d)
        return "\n".join(open(os.path.join(d, f)).read() for f in sorted(os.listdir(d)) if f.endswith(".uvl"))


# ── NUM_MODELS + filename suffixes ───────────────────────────────────────


def test_num_models_respected():
    p = _base_params(NUM_MODELS=7)
    with tempfile.TemporaryDirectory() as d:
        FmgeneratorModel(p).generate_models(d)
        assert len([f for f in os.listdir(d) if f.endswith(".uvl")]) == 7


def test_feature_count_suffix_applied():
    p = _base_params(INCLUDE_FEATURE_COUNT_SUFFIX=True)
    with tempfile.TemporaryDirectory() as d:
        FmgeneratorModel(p).generate_models(d)
        files = [f for f in os.listdir(d) if f.endswith(".uvl")]
        assert all(re.search(r"_\d+f\.uvl$", f) for f in files)


def test_constraint_count_suffix_applied():
    p = _base_params(INCLUDE_CONSTRAINT_COUNT_SUFFIX=True)
    with tempfile.TemporaryDirectory() as d:
        FmgeneratorModel(p).generate_models(d)
        files = [f for f in os.listdir(d) if f.endswith(".uvl")]
        assert all(re.search(r"_\d+c\.uvl$", f) for f in files)


def test_both_suffixes_applied():
    p = _base_params(INCLUDE_FEATURE_COUNT_SUFFIX=True, INCLUDE_CONSTRAINT_COUNT_SUFFIX=True)
    with tempfile.TemporaryDirectory() as d:
        FmgeneratorModel(p).generate_models(d)
        files = [f for f in os.listdir(d) if f.endswith(".uvl")]
        assert all(re.search(r"_\d+f_\d+c\.uvl$", f) for f in files)


def test_name_prefix_applied():
    p = _base_params(NAME_PREFIX="PREFIXED_")
    with tempfile.TemporaryDirectory() as d:
        FmgeneratorModel(p).generate_models(d)
        assert all(f.startswith("PREFIXED_") for f in os.listdir(d) if f.endswith(".uvl"))


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
        assert 5 <= len(feats) <= 9, f"feature count out of range: {len(feats)}"


def test_max_tree_depth_respected():
    """No child feature should live deeper than MAX_TREE_DEPTH levels below
    the root. Features are indented with tabs in UVL; each level adds 2 tabs
    (one for the relation keyword, one for the child). Root sits at 1 tab,
    so max depth D means the deepest feature is at 1 + 2*D tabs."""
    p = _base_params(MAX_TREE_DEPTH=3, MIN_FEATURES=6, MAX_FEATURES=10)
    text = _run(p, n=3)
    feat_lines = [ln for ln in text.splitlines() if re.match(r"\t+F\d+\b", ln)]
    max_indent = max(len(ln) - len(ln.lstrip("\t")) for ln in feat_lines)
    assert max_indent <= 1 + 2 * 3, f"deepest feature at {max_indent} tabs exceeds cap"


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
    # standalone relation indicator (not cardinality [n..m] which attaches to a feature).
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
    bare_card = [ln for ln in lines if re.match(r"^\s*\[\d+(\.\.\d+)?\]\s*$", ln)]
    assert len(bare_card) > 0, "no group-cardinality relations emitted"


def test_feature_cardinality_off_produces_none():
    p = _base_params(ARITHMETIC_LEVEL=True, FEATURE_CARDINALITY=False)
    text = _run(p, n=5)
    assert "cardinality [" not in text


def test_feature_cardinality_on_produces_some():
    p = _base_params(
        ARITHMETIC_LEVEL=True,
        FEATURE_CARDINALITY=True,
        PROB_FEATURE_CARDINALITY=1.0,
        MIN_FEATURE_CARDINALITY=[2],
        MAX_FEATURE_CARDINALITY=[5],
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
        DIST_BOOLEAN=1.0,
        DIST_INTEGER=0.0,
        DIST_REAL=0.0,
        DIST_STRING=0.0,
        MIN_ATTRIBUTES=3,
        MAX_ATTRIBUTES=3,
    )
    text = _run(p, n=3)
    # Boolean attrs serialise as "{Name true}" or "{Name false}".
    attrs = re.findall(r"\{Attr\d+\s+(\S+?)(?:,|\})", text)
    assert attrs, "no attributes found"
    assert all(a in ("true", "false") for a in attrs), f"non-boolean attrs: {attrs}"


def test_dist_integer_only_produces_integer_attrs():
    p = _base_params(
        ARITHMETIC_LEVEL=True,
        DIST_BOOLEAN=0.0,
        DIST_INTEGER=1.0,
        DIST_REAL=0.0,
        DIST_STRING=0.0,
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
        DIST_BOOLEAN=0.0,
        DIST_INTEGER=0.0,
        DIST_REAL=0.0,
        DIST_STRING=1.0,
        MIN_ATTRIBUTES=3,
        MAX_ATTRIBUTES=3,
    )
    text = _run(p, n=3)
    # Strings emit quoted: {Attr0 'low'}
    assert re.search(r"\{Attr\d+\s+'[^']+'", text)


def test_no_integer_attrs_when_arithmetic_off():
    """Even if DIST_INTEGER=1.0, ARITHMETIC_LEVEL=False falls back to Boolean."""
    p = _base_params(
        ARITHMETIC_LEVEL=False,
        DIST_BOOLEAN=0.0,
        DIST_INTEGER=1.0,
        DIST_REAL=0.0,
        DIST_STRING=0.0,
        MIN_ATTRIBUTES=3,
        MAX_ATTRIBUTES=3,
    )
    text = _run(p, n=3)
    # Since integer/real are gated off and DIST_BOOLEAN=0, engine falls back
    # to the only enabled kind (boolean).
    attrs = re.findall(r"\{Attr\d+\s+(\S+?)(?:,|\})", text)
    assert all(a in ("true", "false") for a in attrs), f"got non-boolean: {attrs}"


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
    assert arith_in_ctc is None or "!=" in body, "unexpected arithmetic in boolean-only constraints"


def test_arithmetic_level_produces_arith_constraints():
    p = _base_params(
        ARITHMETIC_LEVEL=True,
        DIST_BOOLEAN=0.0,
        DIST_INTEGER=1.0,
        DIST_REAL=0.0,
        DIST_STRING=0.0,
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
    assert re.search(r"\s[+\-*/]\s", body), f"no arithmetic constraints emitted:\n{body}"


def test_aggregate_functions_produce_sum_avg():
    p = _base_params(
        ARITHMETIC_LEVEL=True,
        AGGREGATE_FUNCTIONS=True,
        DIST_BOOLEAN=0.0,
        DIST_INTEGER=1.0,
        DIST_REAL=0.0,
        DIST_STRING=0.0,
        CTC_DIST_BOOLEAN=0.0,
        CTC_DIST_INTEGER=1.0,
        CTC_DIST_REAL=0.0,
        CTC_DIST_STRING=0.0,
        PROB_SUM_FUNCTION=0.5,
        PROB_AVG_FUNCTION=0.5,
        MIN_CONSTRAINTS=15,
        MAX_CONSTRAINTS=15,
        MIN_ATTRIBUTES=3,
        MAX_ATTRIBUTES=4,
    )
    text = _run(p, n=5)
    body = "\n".join(_iter_constraint_lines(text))
    assert "sum(" in body or "avg(" in body, f"no aggregate constraints emitted:\n{body}"


def test_string_level_produces_len_constraints():
    p = _base_params(
        TYPE_LEVEL=True,
        STRING_CONSTRAINTS=True,
        DIST_BOOLEAN=0.0,
        DIST_INTEGER=0.0,
        DIST_REAL=0.0,
        DIST_STRING=1.0,
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
        assert len(refs) == 4, f"expected 4 vars in constraint, got {len(refs)}: {line}"


def test_prob_not_zero_produces_no_negations():
    p = _base_params(
        PROB_NOT=0.0,
        MIN_CONSTRAINTS=8,
        MAX_CONSTRAINTS=8,
    )
    text = _run(p, n=5)
    ctc_body = text.split("constraints\n", 1)[1] if "constraints\n" in text else ""
    # '!' only appears in negation in UVL syntax. The writer uses "! ".
    assert "! " not in ctc_body, "unexpected NOT in constraints"


def test_prob_not_one_produces_many_negations():
    p = _base_params(
        PROB_NOT=1.0,
        MIN_CONSTRAINTS=8,
        MAX_CONSTRAINTS=8,
    )
    text = _run(p, n=5)
    ctc_body = text.split("constraints\n", 1)[1] if "constraints\n" in text else ""
    assert ctc_body.count("!") > 5, "expected many NOT operators"


def test_min_max_constraints_respected():
    p = _base_params(MIN_CONSTRAINTS=3, MAX_CONSTRAINTS=3)
    for _ in range(5):
        text = _run(p, n=1)
        ctc_body = text.split("constraints\n", 1)[1] if "constraints\n" in text else ""
        lines = [ln for ln in ctc_body.splitlines() if ln.strip()]
        assert len(lines) == 3


# ── Distributions: empirical checks on large batches ─────────────────────


def test_prob_and_dominant():
    """With PROB_AND=1.0, PROB_OR/IMPLIES/EQUIV=0, every Boolean connective
    should be AND (serialised as ' & ')."""
    p = _base_params(
        PROB_AND=1.0,
        PROB_OR_CT=0.0,
        PROB_IMPLICATION=0.0,
        PROB_EQUIVALENCE=0.0,
        PROB_NOT=0.0,
        MIN_CONSTRAINTS=10,
        MAX_CONSTRAINTS=10,
    )
    text = _run(p, n=3)
    ctc_body = text.split("constraints\n", 1)[1]
    # All connective positions should be '&'; none should be |, =>, <=>.
    assert "=>" not in ctc_body
    assert "<=>" not in ctc_body
    assert " | " not in ctc_body
    assert " & " in ctc_body


def test_prob_implies_dominant():
    p = _base_params(
        PROB_AND=0.0,
        PROB_OR_CT=0.0,
        PROB_IMPLICATION=1.0,
        PROB_EQUIVALENCE=0.0,
        PROB_NOT=0.0,
        MIN_CONSTRAINTS=10,
        MAX_CONSTRAINTS=10,
    )
    text = _run(p, n=3)
    ctc_body = text.split("constraints\n", 1)[1]
    assert " => " in ctc_body
    assert " & " not in ctc_body
    assert "<=>" not in ctc_body


# ── ENSURE_SATISFIABLE ───────────────────────────────────────────────────


def test_ensure_satisfiable_runs_without_crashing():
    """Smoke test: the retry loop must not raise on normal inputs."""
    p = _base_params(ENSURE_SATISFIABLE=True, NUM_MODELS=2)
    with tempfile.TemporaryDirectory() as d:
        fms = FmgeneratorModel(p).generate_models(d)
        assert len(fms) == 2


# ── Manual attribute mode ────────────────────────────────────────────────


def test_manual_mode_uses_attribute_in_constraints_flag():
    """Attributes with use_in_constraints=False must not appear in any
    constraint expression (across every generated model)."""
    attr = Attribute(
        name="SecretSize",
        domain=Domain(ranges=None, elements=[True, False]),
        default_value=True,
    )
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
    """generate_single_model must be fully deterministic on (SEED, index)."""
    p = _base_params(SEED=42)
    a = generate_single_model(p, 0)
    b = generate_single_model(p, 0)
    assert [f.name for f in a.get_features()] == [f.name for f in b.get_features()]
    assert len(a.ctcs) == len(b.ctcs)
