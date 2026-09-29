"""End-to-end wizard-to-output tests.

Each test drives the full 6-step wizard (step1 batch → step2 levels →
step3 tree → step4 constraints → step5 attributes → step6 output), then
pulls the resulting generator parameters via /generator/random/params-json and feeds
it straight into the vendored FmgeneratorModel — the same code Pyodide
runs in the browser. The generated UVL is parsed and the content is
asserted against what the user selected in the wizard.

This is the contract the user cares about: every knob you touch must
show up in the .uvl files (or be absent when you disabled its level).
"""

import json
import re
from itertools import product
from types import SimpleNamespace

import pytest
from flamapy.metamodels.fm_generator.models import FmgeneratorModel
from flamapy.metamodels.fm_generator.operations import GenerateFeatureModel
from flamapy.metamodels.fm_metamodel.models.feature_model import FeatureModel
from flamapy.metamodels.fm_metamodel.transformations.uvl_reader import UVLReader
from flamapy.metamodels.fm_metamodel.transformations.uvl_writer import UVLWriter
from flamapy.metamodels.pysat_metamodel.operations import PySATSatisfiable
from flamapy.metamodels.pysat_metamodel.transformations.fm_to_pysat import (
    FmToPysat,
)

import app.features.generator.wizard as wizard
from app.features.generator.assets.js import fmgen_wrapper
from app.features.generator.assets.js.fmgen_wrapper import _build_one
from app.features.generator.wizard import GeneratorWizardService

pytestmark = pytest.mark.integration

# ── Fixtures & helpers ───────────────────────────────────────────────────


@pytest.fixture
def client(test_app):
    """Per-test Flask client so sessions don't leak between tests."""
    with test_app.test_client() as c:
        yield c


_REL_EVEN = {
    "dist_optional": "0.3",
    "dist_mandatory": "0.3",
    "dist_alternative": "0.2",
    "dist_or": "0.2",
}
_BOOLOP_EVEN = {
    "prob_and": "0.4",
    "prob_or": "0.2",
    "prob_implies": "0.2",
    "prob_equiv": "0.2",
}
_ARITH_EVEN = {"prob_plus": "0.4", "prob_minus": "0.3", "prob_times": "0.2", "prob_div": "0.1"}
_CMP_EVEN = {"prob_eq": "0.2", "prob_lt": "0.2", "prob_gt": "0.2", "prob_leq": "0.2", "prob_geq": "0.2"}


def _step1(num_models="3", seed="42", name_prefix="fm"):
    return {"num_models_val": num_models, "seed": seed, "name_prefix": name_prefix}


def _step2(*, arithmetic=False, type_=False, group_card=False, feat_card=False, aggregate=False, string_ctc=False):
    d = {}
    if arithmetic:
        d["arithmetic_level"] = "on"
    if type_:
        d["type_level"] = "on"
    if group_card:
        d["group_cardinality"] = "on"
    if feat_card:
        d["feature_cardinality"] = "on"
    if aggregate:
        d["aggregate_functions"] = "on"
    if string_ctc:
        d["string_constraints"] = "on"
    return d


def _step3(*, group_card=False, feat_card=False, extras=None):
    d = {
        "num_features_min": "6",
        "num_features_max": "10",
        "max_tree_depth": "3",
        **_REL_EVEN,
        "dist_group_cardinality": "0.0",
        "nav": "next",
    }
    if group_card:
        # Redistribute evenly across 5 relation families.
        d.update(
            {
                "dist_optional": "0.2",
                "dist_mandatory": "0.2",
                "dist_alternative": "0.2",
                "dist_or": "0.2",
                "dist_group_cardinality": "0.2",
                "group_cardinality_min": "1",
                "group_cardinality_max": "5",
            }
        )
    if feat_card:
        d.update(
            {
                "prob_fc": "0.3",
                "min_feature_cardinality": "2",
                "max_feature_cardinality": "5",
            }
        )
    if extras:
        d.update(extras)
    return d


def _step4(*, arithmetic=False, aggregate=False, string=False, extras=None):
    d = {
        "num_constraints_min": "6",
        "num_constraints_max": "8",
        "extra_constraint_repr": "1",
        "vars_per_ctc_min": "2",
        "vars_per_ctc_max": "3",
        "prob_not": "0.3",
        **_BOOLOP_EVEN,
        "nav": "next",
    }
    # TYPE_LEVEL implicitly forces ARITHMETIC_LEVEL on in the generator model,
    # so a string-only test scenario still needs arithmetic probability
    # fields to satisfy the step 4 validator.
    effective_arith = arithmetic or string
    if effective_arith:
        d["arithmetic_level"] = "on"
        d.update(_ARITH_EVEN)
        if aggregate:
            d["aggregate_functions"] = "on"
            d.update(
                {
                    "prob_plus": "0.3",
                    "prob_minus": "0.2",
                    "prob_times": "0.1",
                    "prob_div": "0.1",
                    "prob_sum": "0.2",
                    "prob_avg": "0.1",
                }
            )
        d.update(_CMP_EVEN)
    if string:
        d["type_level"] = "on"
        d["string_constraints"] = "on"
        d["prob_len"] = "1.0"
    # CTC type distribution is required whenever a non-boolean level is on.
    if effective_arith or string:
        ctc = {"ctc_dist_boolean": "0.5", "ctc_dist_integer": "0.0", "ctc_dist_real": "0.0", "ctc_dist_string": "0.0"}
        if effective_arith and not string:
            ctc["ctc_dist_integer"] = "0.5"
        if string:
            if arithmetic:
                ctc.update({"ctc_dist_boolean": "0.4", "ctc_dist_integer": "0.4", "ctc_dist_string": "0.2"})
            else:
                ctc.update({"ctc_dist_boolean": "0.5", "ctc_dist_string": "0.5"})
        d.update(ctc)
    if extras:
        d.update(extras)
    return d


def _step5(*, extras=None):
    """Default: all-boolean attrs. Tests enabling levels should override."""
    d = {
        "random_attributes": "on",
        "min_attributes": "2",
        "max_attributes": "4",
        "dist_boolean_atr": "1.0",
        "dist_integer_atr": "0.0",
        "dist_real_atr": "0.0",
        "dist_string_atr": "0.0",
        "nav": "next",
    }
    if extras:
        d.update(extras)
    return d


def _step6(*, ensure_satisfiable=False, feat_suffix=False, ctc_suffix=False):
    d = {"nav": "next"}
    if ensure_satisfiable:
        d["ensure_satisfiable"] = "on"
    if feat_suffix:
        d["feature_count_suffix"] = "on"
    if ctc_suffix:
        d["constraint_count_suffix"] = "on"
    return d


def _walk_wizard(client, step1=None, step2=None, step3=None, step4=None, step5=None, step6=None):
    r = client.post("/generator/random/step1", data=step1 or _step1())
    assert r.status_code == 302, f"step1 failed: {r.status_code}\n{r.data[:400]!r}"
    r = client.post("/generator/random/step2", data=step2 or _step2())
    assert r.status_code == 302, f"step2 failed: {r.status_code}\n{r.data[:400]!r}"
    r = client.post("/generator/random/step3", data=step3 or _step3())
    assert r.status_code == 302, f"step3 failed: {r.status_code}\n{r.data[:400]!r}"
    r = client.post("/generator/random/step4", data=step4 or _step4())
    assert r.status_code == 302, f"step4 failed: {r.status_code}\n{r.data[:400]!r}"
    r = client.post("/generator/random/step5", data=step5 or _step5())
    assert r.status_code == 302, f"step5 failed: {r.status_code}\n{r.data[:400]!r}"
    r = client.post("/generator/random/step6", data=step6 or _step6())
    assert r.status_code == 302, f"step6 failed: {r.status_code}\n{r.data[:400]!r}"
    return r


def _prepend_uvl_includes(serialized_model: str, includes: list[str]) -> str:
    if not includes:
        return serialized_model

    include_block = "include\n" + "\n".join(f"\t{inc}" for inc in includes) + "\n"
    return include_block + serialized_model


def _serialize_uvl(fm: FeatureModel) -> str:
    serialized_model = UVLWriter(None, fm).transform()
    return _prepend_uvl_includes(serialized_model, getattr(fm, "uvl_includes", []))


def _filename_for(model: FmgeneratorModel, fm: FeatureModel, index: int) -> str:
    base_name = (model.naming.name_prefix or "").strip() or "fm"

    include_features = model.naming.include_feature_count_suffix
    include_constraints = model.naming.include_constraint_count_suffix

    feature_count = len(list(fm.get_features()))
    constraint_count = len(getattr(fm, "ctcs", []))

    if include_features and include_constraints:
        return f"{base_name}_{feature_count}f_{constraint_count}c.uvl"

    if include_features:
        return f"{base_name}_{feature_count}f.uvl"

    if include_constraints:
        return f"{base_name}_{constraint_count}c.uvl"

    if model.num_models > 1:
        return f"{base_name}_{index}.uvl"

    return f"{base_name}.uvl"


def _fetch_model_from_wizard(client, n: int | None = None) -> FmgeneratorModel:
    r = client.get("/generator/random/params-json")
    assert r.status_code == 200

    params_dict = json.loads(r.data)

    if n is not None:
        params_dict["NUM_MODELS"] = n

    return FmgeneratorModel.from_flat_dict(params_dict)


def _fetch_params_and_generate(client, n=3):
    model = _fetch_model_from_wizard(client, n=n)

    return "\n".join(
        _serialize_uvl(GenerateFeatureModel().execute(model, index=index).get_result())
        for index in range(model.num_models)
    )


def _iter_ctc_lines(text):
    in_ctc = False
    for ln in text.splitlines():
        if ln == "features":
            in_ctc = False
            continue
        if ln == "constraints":
            in_ctc = True
            continue
        if in_ctc and ln.strip():
            yield ln.strip()


def _o1_level_combinations():
    cases = []

    # Nivel Booleano: group cardinality es el único minor level compatible.
    for group_card in (False, True):
        cases.append(
            pytest.param(
                "boolean",
                group_card,
                False,
                False,
                False,
                id=f"boolean-group-{group_card}",
            )
        )

    # Nivel Aritmético: group cardinality, feature cardinality y agregados.
    for group_card, feature_card, aggregate in product(
        (False, True),
        repeat=3,
    ):
        cases.append(
            pytest.param(
                "arithmetic",
                group_card,
                feature_card,
                aggregate,
                False,
                id=(
                    "arithmetic-" f"group-{group_card}-" f"feature-cardinality-{feature_card}-" f"aggregate-{aggregate}"
                ),
            )
        )

    # Nivel Tipo: incluye las combinaciones anteriores y string constraints.
    for group_card, feature_card, aggregate, string_ctc in product(
        (False, True),
        repeat=4,
    ):
        cases.append(
            pytest.param(
                "type",
                group_card,
                feature_card,
                aggregate,
                string_ctc,
                id=(
                    "type-"
                    f"group-{group_card}-"
                    f"feature-cardinality-{feature_card}-"
                    f"aggregate-{aggregate}-"
                    f"string-{string_ctc}"
                ),
            )
        )

    return cases


# ── Happy-path combos ────────────────────────────────────────────────────


def test_boolean_only_wizard_produces_only_boolean(client):
    _walk_wizard(client)
    text = _fetch_params_and_generate(client, n=3)
    body = "\n".join(_iter_ctc_lines(text))
    assert "sum(" not in body
    assert "avg(" not in body
    assert "len(" not in body
    assert not re.search(r"\s[+\-*/]\s", body)


def test_arithmetic_level_wizard_produces_arithmetic_constraints(client):
    _walk_wizard(
        client,
        step2=_step2(arithmetic=True),
        step4=_step4(
            arithmetic=True,
            extras={
                "ctc_dist_boolean": "0.0",
                "ctc_dist_integer": "1.0",
                "ctc_dist_real": "0.0",
                "ctc_dist_string": "0.0",
            },
        ),
        step5=_step5(
            extras={
                "dist_boolean_atr": "0.0",
                "dist_integer_atr": "1.0",
                "dist_real_atr": "0.0",
                "dist_string_atr": "0.0",
                "min_attributes": "3",
                "max_attributes": "4",
            }
        ),
    )
    body = "\n".join(_iter_ctc_lines(_fetch_params_and_generate(client, n=3)))
    assert re.search(r"\s[+\-*/]\s", body), f"no arith ctc:\n{body}"


def test_arithmetic_constraints_do_not_compare_same_expression(client):
    """
    Generated arithmetic constraints must not compare the same expression
    on both sides of a comparator.

    Examples that must never appear:
        F1 < F1
        F2.Attr0 >= F2.Attr0
        len(F3) == len(F3)
    """
    _walk_wizard(
        client,
        step2=_step2(arithmetic=True),
        step3=_step3(
            extras={
                "num_features_min": "15",
                "num_features_max": "20",
            }
        ),
        step4=_step4(
            arithmetic=True,
            extras={
                "num_constraints_min": "20",
                "num_constraints_max": "20",
                "ctc_dist_boolean": "0.0",
                "ctc_dist_integer": "1.0",
                "ctc_dist_real": "0.0",
                "ctc_dist_string": "0.0",
                "prob_eq": "0.2",
                "prob_lt": "0.2",
                "prob_gt": "0.2",
                "prob_leq": "0.2",
                "prob_geq": "0.2",
            },
        ),
        step5=_step5(
            extras={
                "dist_boolean_atr": "0.0",
                "dist_integer_atr": "1.0",
                "dist_real_atr": "0.0",
                "dist_string_atr": "0.0",
                "min_attributes": "5",
                "max_attributes": "5",
            }
        ),
    )

    body = "\n".join(_iter_ctc_lines(_fetch_params_and_generate(client, n=5)))

    forbidden_patterns = [
        r"\b(F\d+(?:\.Attr\d+)?)\s*(==|<|>|<=|>=)\s*\1\b",
        r"\blen\((F\d+(?:\.Attr\d+)?)\)\s*(==|<|>|<=|>=)\s*len\(\1\)",
    ]

    for pattern in forbidden_patterns:
        match = re.search(pattern, body)

        assert not match, (
            "Found trivial self-comparison in generated constraints:\n"
            f"{match.group(0)}\n\n"
            f"Full constraints:\n{body}"
        )


def test_aggregate_functions_never_generate_more_than_two_arguments(client):
    _walk_wizard(
        client,
        step2=_step2(arithmetic=True, aggregate=True),
        step4=_step4(
            arithmetic=True,
            aggregate=True,
            extras={
                "prob_plus": "0.0",
                "prob_minus": "0.0",
                "prob_times": "0.0",
                "prob_div": "0.0",
                "prob_sum": "0.5",
                "prob_avg": "0.5",
                "ctc_dist_boolean": "0.0",
                "ctc_dist_integer": "1.0",
                "ctc_dist_real": "0.0",
                "ctc_dist_string": "0.0",
                "num_constraints_min": "20",
                "num_constraints_max": "20",
            },
        ),
        step5=_step5(
            extras={
                "dist_boolean_atr": "0.0",
                "dist_integer_atr": "1.0",
                "dist_real_atr": "0.0",
                "dist_string_atr": "0.0",
                "min_attributes": "5",
                "max_attributes": "5",
            }
        ),
    )

    body = "\n".join(_iter_ctc_lines(_fetch_params_and_generate(client, n=5)))

    aggregate_lines = [line for line in body.splitlines() if "sum(" in line or "avg(" in line]

    assert aggregate_lines, f"no aggregate functions generated:\n{body}"

    for line in aggregate_lines:
        for function in ("sum(", "avg("):
            if function in line:
                start = line.index(function) + len(function)
                end = line.index(")", start)

                args = [arg.strip() for arg in line[start:end].split(",") if arg.strip()]

                assert len(args) <= 2, f"invalid aggregate function with more than two " f"arguments: {line}"


# ── Level-coherence: changing step2 rewrites later step behaviour ───────


def test_arithmetic_off_means_no_arithmetic_in_output(client):
    _walk_wizard(
        client,
        step2=_step2(),  # no arithmetic
        step4={**_step4(), "prob_plus": "0.7", "prob_minus": "0.2", "prob_times": "0.1", "prob_div": "0.0"},
    )
    body = "\n".join(_iter_ctc_lines(_fetch_params_and_generate(client, n=3)))
    assert not re.search(r"\s[+\-*/]\s", body)


def test_type_off_means_no_string_ctc(client):
    _walk_wizard(client, step2=_step2(arithmetic=True), step4=_step4(arithmetic=True))
    body = "\n".join(_iter_ctc_lines(_fetch_params_and_generate(client, n=3)))
    assert "len(" not in body


def test_feature_cardinality_off_means_no_cardinality_in_uvl(client):
    _walk_wizard(client, step2=_step2(arithmetic=True), step4=_step4(arithmetic=True))
    text = _fetch_params_and_generate(client, n=3)
    assert "cardinality [" not in text


def test_feature_cardinality_on_produces_cardinality(client):
    _walk_wizard(
        client,
        step2=_step2(arithmetic=True, feat_card=True),
        step3=_step3(feat_card=True, extras={"prob_fc": "1.0"}),
        step4=_step4(arithmetic=True),
    )
    text = _fetch_params_and_generate(client, n=2)
    assert "cardinality [" in text


def test_group_cardinality_off_keeps_only_standard_relations(client):
    _walk_wizard(client)
    text = _fetch_params_and_generate(client, n=3)
    bare = [ln for ln in text.splitlines() if re.match(r"^\s*\[\d+(\.\.\d+)?\]\s*$", ln)]
    assert not bare


def test_group_cardinality_on_produces_groups(client):
    _walk_wizard(
        client,
        step2=_step2(group_card=True),
        step3=_step3(
            group_card=True,
            extras={
                "dist_optional": "0.0",
                "dist_mandatory": "0.0",
                "dist_alternative": "0.0",
                "dist_or": "0.0",
                "dist_group_cardinality": "1.0",
                "num_features_min": "8",
                "num_features_max": "12",
            },
        ),
    )
    text = _fetch_params_and_generate(client, n=3)
    bare = [ln for ln in text.splitlines() if re.match(r"^\s*\[\d+(\.\.\d+)?\]\s*$", ln)]
    assert bare, f"no group cardinality relations:\n{text}"


# ── Individual parameter plumbing ────────────────────────────────────────


def test_ctc_dist_weights_force_string(client):
    _walk_wizard(
        client,
        step2=_step2(type_=True, string_ctc=True),
        step4=_step4(
            string=True,
            extras={
                "ctc_dist_boolean": "0.0",
                "ctc_dist_integer": "0.0",
                "ctc_dist_real": "0.0",
                "ctc_dist_string": "1.0",
            },
        ),
        step5=_step5(
            extras={
                "dist_boolean_atr": "0.0",
                "dist_integer_atr": "0.0",
                "dist_real_atr": "0.0",
                "dist_string_atr": "1.0",
                "min_attributes": "3",
                "max_attributes": "4",
            }
        ),
    )
    lines = [
        ln
        for ln in _iter_ctc_lines(_fetch_params_and_generate(client, n=3))
        if not ln.startswith("include") and not ln.startswith("Type.")
    ]
    assert all("len(" in ln or re.search(r"\.Attr\d+\s*==", ln) for ln in lines)


# ═══════════════════════════════════════════════════════════════════════
# PARAMETRISED MASS COVERAGE
# ═══════════════════════════════════════════════════════════════════════


# ── Step 3: feature cardinality bounds ──────────────────────────────────


@pytest.mark.parametrize(
    "fmin,fmax",
    [("2", "2"), ("2", "5"), ("3", "7"), ("1", "3"), ("5", "10"), ("2", "20")],
)
def test_feature_cardinality_bounds_observed(client, fmin, fmax):
    _walk_wizard(
        client,
        step2=_step2(arithmetic=True, feat_card=True),
        step3=_step3(
            feat_card=True,
            extras={
                "prob_fc": "1.0",
                "min_feature_cardinality": fmin,
                "max_feature_cardinality": fmax,
                "num_features_min": "6",
                "num_features_max": "8",
            },
        ),
        step4=_step4(arithmetic=True),
    )
    text = _fetch_params_and_generate(client, n=3)
    for lo, hi in re.findall(r"cardinality \[(\d+)\.\.(\d+)\]", text):
        lo, hi = int(lo), int(hi)
        assert int(fmin) <= lo <= hi <= int(fmax), f"cardinality [{lo}..{hi}] outside [{fmin}..{fmax}]"


# ── Step 4: constraint counts ───────────────────────────────────────────


@pytest.mark.parametrize("fixed", ["1", "3", "5", "7", "10"])
def test_fixed_constraint_count_observed(client, fixed):
    _walk_wizard(client, step4=_step4(extras={"num_constraints_min": fixed, "num_constraints_max": fixed}))
    text = _fetch_params_and_generate(client, n=2)
    for model_text in text.split("features\n")[1:]:
        ctcs = list(_iter_ctc_lines("features\n" + model_text))
        assert len(ctcs) == int(fixed)


@pytest.mark.parametrize("fixed", ["2", "3", "4", "5"])
def test_fixed_vars_per_ctc_observed(client, fixed):
    _walk_wizard(
        client,
        step3=_step3(extras={"num_features_min": "15", "num_features_max": "20"}),
        step4=_step4(extras={"vars_per_ctc_min": fixed, "vars_per_ctc_max": fixed}),
    )
    text = _fetch_params_and_generate(client, n=2)
    for line in _iter_ctc_lines(text):
        refs = re.findall(r"\bF\d+\b", line)
        assert len(refs) == int(fixed), f"expected {fixed} vars, got {len(refs)}: {line}"


# ── Step 5: attribute count bounds ──────────────────────────────────────


@pytest.mark.parametrize("fixed", ["1", "2", "3", "5", "7"])
def test_attribute_fixed_count_observed(client, fixed):
    _walk_wizard(
        client,
        step5=_step5(
            extras={
                "min_attributes": fixed,
                "max_attributes": fixed,
            }
        ),
    )
    text = _fetch_params_and_generate(client, n=3)
    for model_text in text.split("features\n")[1:]:
        attrs = set(re.findall(r"\bAttr(\d+)\b", model_text))
        assert attrs == set(str(i) for i in range(int(fixed))), f"expected {fixed} attrs, got {sorted(attrs)}"


# ── Step 5: attribute type distribution ─────────────────────────────────


@pytest.mark.parametrize(
    "dist,kind",
    [
        (
            {
                "dist_boolean_atr": "1.0",
                "dist_integer_atr": "0.0",
                "dist_real_atr": "0.0",
                "dist_string_atr": "0.0",
            },
            "boolean",
        ),
        (
            {
                "dist_boolean_atr": "0.0",
                "dist_integer_atr": "1.0",
                "dist_real_atr": "0.0",
                "dist_string_atr": "0.0",
            },
            "integer",
        ),
        (
            {
                "dist_boolean_atr": "0.0",
                "dist_integer_atr": "0.0",
                "dist_real_atr": "1.0",
                "dist_string_atr": "0.0",
            },
            "real",
        ),
        (
            {
                "dist_boolean_atr": "0.0",
                "dist_integer_atr": "0.0",
                "dist_real_atr": "0.0",
                "dist_string_atr": "1.0",
            },
            "string",
        ),
    ],
)
def test_attribute_type_dominance(client, dist, kind):
    arith = kind in ("integer", "real")
    type_ = kind == "string"
    _walk_wizard(
        client,
        step2=_step2(arithmetic=arith, type_=type_, string_ctc=type_),
        step4=_step4(arithmetic=arith, string=type_),
        step5=_step5(extras={**dist, "min_attributes": "3", "max_attributes": "3"}),
    )
    text = _fetch_params_and_generate(client, n=3)
    attrs = re.findall(r"\{Attr\d+\s+([^,}]+)", text)
    assert attrs
    for v in attrs:
        v = v.strip()
        if kind == "boolean":
            assert v in ("true", "false"), v
        elif kind == "integer":
            assert re.match(r"^-?\d+$", v), v
        elif kind == "real":
            assert re.match(r"^-?\d+\.\d+$", v), v
        elif kind == "string":
            assert v.startswith("'") and v.endswith("'"), v


# ── Determinism across wizard posts ─────────────────────────────────────


@pytest.mark.parametrize("seed", ["1", "7", "42", "1234", "99999"])
def test_same_seed_gives_same_models(client, seed):
    _walk_wizard(client, step1=_step1(seed=seed))
    text1 = _fetch_params_and_generate(client, n=3)
    with client.application.test_client() as c2:
        _walk_wizard(c2, step1=_step1(seed=seed))
        text2 = _fetch_params_and_generate(c2, n=3)
    assert text1 == text2


# ── Back-navigation coherence ────────────────────────────────────────────


@pytest.mark.parametrize(
    "from_step,back_url",
    [
        (2, "/step1"),
        (3, "/step2"),
        (4, "/step3"),
        (5, "/step4"),
        (6, "/step5"),
    ],
)
def test_prev_nav_goes_to_previous_step(client, from_step, back_url):
    _walk_wizard(client)
    # Re-visit the "from" step and post prev.
    payloads = {
        2: _step2(),
        3: _step3(),
        4: _step4(),
        5: _step5(),
        6: _step6(),
    }
    data = dict(payloads[from_step])
    data["nav"] = "prev"
    r = client.post(f"/generator/random/step{from_step}", data=data)
    assert r.status_code == 302
    assert r.location.endswith(back_url), f"prev from step{from_step} → {r.location}"


def test_back_navigation_preserves_all_choices(client):
    """Full back→forward loop must not drop any field along the way."""
    _walk_wizard(
        client,
        step1=_step1(num_models="7", seed="99", name_prefix="pre_"),
        step2=_step2(arithmetic=True, feat_card=True, aggregate=True),
        step3=_step3(
            feat_card=True,
            extras={
                "num_features_min": "8",
                "num_features_max": "15",
                "max_tree_depth": "4",
                "prob_fc": "0.5",
                "min_feature_cardinality": "3",
                "max_feature_cardinality": "6",
            },
        ),
        step4=_step4(
            arithmetic=True,
            aggregate=True,
            extras={
                "num_constraints_min": "4",
                "num_constraints_max": "6",
                "vars_per_ctc_min": "2",
                "vars_per_ctc_max": "4",
            },
        ),
        step5=_step5(
            extras={
                "dist_boolean_atr": "0.4",
                "dist_integer_atr": "0.3",
                "dist_real_atr": "0.3",
                "dist_string_atr": "0.0",
                "min_attributes": "3",
                "max_attributes": "5",
            }
        ),
        step6=_step6(ensure_satisfiable=True, feat_suffix=True, ctc_suffix=True),
    )
    params = json.loads(client.get("/generator/random/params-json").data)
    assert params["NUM_MODELS"] == 7
    assert params["SEED"] == 99
    assert params["NAME_PREFIX"] == "pre_"
    assert params["ARITHMETIC_LEVEL"] is True
    assert params["FEATURE_CARDINALITY"] is True
    assert params["AGGREGATE_FUNCTIONS"] is True
    assert params["MIN_FEATURES"] == 8
    assert params["MAX_FEATURES"] == 15
    assert params["MAX_TREE_DEPTH"] == 4
    assert params["MIN_CONSTRAINTS"] == 4
    assert params["MAX_CONSTRAINTS"] == 6
    assert params["MIN_VARS_PER_CONSTRAINT"] == 2
    assert params["MIN_ATTRIBUTES"] == 3
    assert params["MAX_ATTRIBUTES"] == 5
    assert params["ATTR_DIST_INTEGER"] == pytest.approx(0.3)
    assert params["ENSURE_SATISFIABLE"] is True
    assert params["INCLUDE_FEATURE_COUNT_SUFFIX"] is True


# ── Mixed levels integration ────────────────────────────────────────────


def test_ensure_satisfiable_retries_until_sat(client, monkeypatch):
    _walk_wizard(
        client,
        step6=_step6(ensure_satisfiable=True),
    )
    params = json.loads(client.get("/generator/random/params-json").data)
    params["NUM_MODELS"] = 1
    calls = []

    def fake_sat(feature_model):

        calls.append(feature_model)

        # Primer intento falla
        # Segundo intento pasa
        return len(calls) >= 2

    monkeypatch.setattr(
        GeneratorWizardService,
        "is_satisfiable",
        staticmethod(fake_sat),
    )

    results = GeneratorWizardService.generate_sat_models(params)

    assert results

    # At least two models must be tested
    assert len(calls) == 2


@pytest.mark.parametrize(
    (
        "level",
        "group_card",
        "feature_card",
        "aggregate",
        "string_ctc",
    ),
    _o1_level_combinations(),
)
def test_o1_level_combinations_roundtrip_to_uvl_and_boolean_sat(
    client,
    tmp_path,
    level,
    group_card,
    feature_card,
    aggregate,
    string_ctc,
):
    """O1: cada combinación válida se genera, se serializa y se vuelve a
    leer como UVL. Las variantes booleanas también se transforman a PySAT."""
    num_models = 3
    arithmetic = level in {"arithmetic", "type"}
    type_level = level == "type"

    if string_ctc:
        step4_extras = {
            "ctc_dist_boolean": "0.0",
            "ctc_dist_integer": "0.0",
            "ctc_dist_real": "0.0",
            "ctc_dist_string": "1.0",
        }
        step5_extras = {
            "dist_boolean_atr": "0.0",
            "dist_integer_atr": "0.0",
            "dist_real_atr": "0.0",
            "dist_string_atr": "1.0",
        }
    elif arithmetic:
        step4_extras = {
            "ctc_dist_boolean": "0.0",
            "ctc_dist_integer": "1.0",
            "ctc_dist_real": "0.0",
            "ctc_dist_string": "0.0",
        }
        step5_extras = {
            "dist_boolean_atr": "0.0",
            "dist_integer_atr": "1.0",
            "dist_real_atr": "0.0",
            "dist_string_atr": "0.0",
        }
    else:
        step4_extras = {}
        step5_extras = {}

    _walk_wizard(
        client,
        step1=_step1(num_models=str(num_models), seed="2026"),
        step2=_step2(
            arithmetic=arithmetic,
            type_=type_level,
            group_card=group_card,
            feat_card=feature_card,
            aggregate=aggregate,
            string_ctc=string_ctc,
        ),
        step3=_step3(
            group_card=group_card,
            feat_card=feature_card,
        ),
        step4=_step4(
            arithmetic=arithmetic,
            aggregate=aggregate,
            string=string_ctc,
            extras=step4_extras,
        ),
        step5=_step5(extras=step5_extras),
        step6=_step6(
            ensure_satisfiable=level == "boolean",
        ),
    )

    model = _fetch_model_from_wizard(client)

    assert model.num_models == num_models

    for index in range(num_models):
        generated_model = _build_one(model, index)
        uvl_path = tmp_path / f"{level}_{index}.uvl"

        uvl_path.write_text(
            _serialize_uvl(generated_model),
            encoding="utf-8",
        )

        reloaded_model = UVLReader(str(uvl_path)).transform()

        assert reloaded_model is not None
        assert len(list(reloaded_model.get_features())) > 0

        if level == "boolean":
            pysat_model = FmToPysat(reloaded_model).transform()
            satisfiable_operation = PySATSatisfiable()
            satisfiable_operation.execute(pysat_model)

            assert satisfiable_operation.get_result() in (True, False)


# ── fmgen_wrapper direct contract ─────────────────────────────────────────


@pytest.mark.parametrize(
    ("includes", "expected"),
    [
        ([], "features\n\tF0"),
        (["Boolean.uvl"], "include\n\tBoolean.uvl\nfeatures\n\tF0"),
        (
            ["Boolean.uvl", "Arithmetic.uvl"],
            "include\n\tBoolean.uvl\n\tArithmetic.uvl\nfeatures\n\tF0",
        ),
    ],
)
def test_wrapper_prepends_uvl_includes(includes, expected):
    assert fmgen_wrapper._prepend_uvl_includes("features\n\tF0", includes) == expected


def test_wrapper_serializes_uvl_and_reads_includes(monkeypatch):
    class FakeWriter:
        def __init__(self, path, feature_model):
            assert path is None
            assert feature_model is fm

        def transform(self):
            return "features\n\tF0"

    fm = SimpleNamespace(uvl_includes=["Boolean.uvl"])
    monkeypatch.setattr(fmgen_wrapper, "UVLWriter", FakeWriter)

    result = fmgen_wrapper._serialize_uvl(fm)

    assert result == "include\n\tBoolean.uvl\nfeatures\n\tF0"


def test_wrapper_serializes_uvl_without_includes_attribute(monkeypatch):
    class FakeWriter:
        def __init__(self, path, feature_model):
            pass

        def transform(self):
            return "features\n\tF0"

    monkeypatch.setattr(fmgen_wrapper, "UVLWriter", FakeWriter)

    assert fmgen_wrapper._serialize_uvl(SimpleNamespace()) == "features\n\tF0"


@pytest.mark.parametrize(
    (
        "prefix",
        "feature_suffix",
        "constraint_suffix",
        "num_models",
        "index",
        "expected",
    ),
    [
        ("custom", True, True, 1, 0, "custom_3f_2c.uvl"),
        ("custom", True, False, 1, 0, "custom_3f.uvl"),
        ("custom", False, True, 1, 0, "custom_2c.uvl"),
        ("custom", False, False, 3, 2, "custom_2.uvl"),
        ("custom", False, False, 1, 0, "custom.uvl"),
        ("   ", False, False, 1, 0, "fm.uvl"),
    ],
)
def test_wrapper_builds_expected_filename(
    prefix,
    feature_suffix,
    constraint_suffix,
    num_models,
    index,
    expected,
):
    model = SimpleNamespace(
        naming=SimpleNamespace(
            name_prefix=prefix,
            include_feature_count_suffix=feature_suffix,
            include_constraint_count_suffix=constraint_suffix,
        ),
        num_models=num_models,
    )
    fm = SimpleNamespace(
        get_features=lambda: ["F0", "F1", "F2"],
        ctcs=["c1", "c2"],
    )

    assert fmgen_wrapper._filename_for(model, fm, index) == expected


def test_wrapper_generates_feature_model_with_received_arguments(monkeypatch):
    result = object()
    operations = []

    class FakeOperation:
        def __init__(self):
            operations.append(self)
            self.execute_args = None

        def execute(self, **kwargs):
            self.execute_args = kwargs

        def get_result(self):
            return result

    model = object()
    monkeypatch.setattr(fmgen_wrapper, "GenerateFeatureModel", FakeOperation)

    assert fmgen_wrapper._generate_feature_model(model, index=4, attempt=2) is result
    assert operations[0].execute_args == {
        "model": model,
        "index": 4,
        "attempt": 2,
    }


def test_wrapper_build_one_delegates_to_feature_model_generator(monkeypatch):
    model = object()
    result = object()
    calls = []

    def fake_generate(received_model, index):
        calls.append((received_model, index))
        return result

    monkeypatch.setattr(fmgen_wrapper, "_generate_feature_model", fake_generate)

    assert fmgen_wrapper._build_one(model, 3) is result
    assert calls == [(model, 3)]


def test_wrapper_generate_models_returns_serialized_batch(monkeypatch):
    model = SimpleNamespace(num_models=2)
    params = {"SEED": 42}
    built_indexes = []

    monkeypatch.setattr(
        fmgen_wrapper,
        "FmgeneratorModel",
        SimpleNamespace(from_flat_dict=lambda received: model),
    )
    monkeypatch.setattr(
        fmgen_wrapper,
        "_build_one",
        lambda received_model, index: built_indexes.append(index) or f"fm-{index}",
    )
    monkeypatch.setattr(
        fmgen_wrapper,
        "_serialize_uvl",
        lambda fm: f"uvl-{fm}",
    )

    result = fmgen_wrapper.generate_models(json.dumps(params))

    assert json.loads(result) == ["uvl-fm-0", "uvl-fm-1"]
    assert built_indexes == [0, 1]


def test_wrapper_generate_one_model_returns_download_payload(monkeypatch):
    model = SimpleNamespace(num_models=3)
    fm = SimpleNamespace(
        get_features=lambda: ["F0", "F1", "F2"],
        ctcs=["c1", "c2"],
    )
    calls = []

    monkeypatch.setattr(
        fmgen_wrapper,
        "FmgeneratorModel",
        SimpleNamespace(from_flat_dict=lambda received: model),
    )

    def fake_build_one(received_model, index):
        calls.append(("build", received_model, index))
        return fm

    def fake_filename(received_model, received_fm, index):
        calls.append(("filename", received_model, received_fm, index))
        return "custom.uvl"

    monkeypatch.setattr(fmgen_wrapper, "_build_one", fake_build_one)
    monkeypatch.setattr(fmgen_wrapper, "_filename_for", fake_filename)
    monkeypatch.setattr(fmgen_wrapper, "_serialize_uvl", lambda received_fm: "uvl-content")

    result = fmgen_wrapper.generate_one_model(json.dumps({"SEED": 42}), "2")

    assert json.loads(result) == {
        "filename": "custom.uvl",
        "content": "uvl-content",
        "features": 3,
        "constraints": 2,
    }
    assert calls == [
        ("build", model, 2),
        ("filename", model, fm, 2),
    ]


def test_serialize_generated_model_covers_all_filename_branches(
    monkeypatch,
):
    class FakeWriter:
        def __init__(self, _, feature_model):
            self.feature_model = feature_model

        def transform(self):
            return "root Root {}"

    monkeypatch.setattr(wizard, "UVLWriter", FakeWriter)

    feature_model = SimpleNamespace(
        get_features=lambda: [1, 2, 3],
        ctcs=[1],
    )

    cases = (
        (True, True, 1, "demo_3f_1c.uvl"),
        (True, False, 1, "demo_3f.uvl"),
        (False, True, 1, "demo_1c.uvl"),
        (False, False, 2, "demo_4.uvl"),
    )

    for feature_suffix, constraint_suffix, num_models, expected in cases:
        model = SimpleNamespace(
            num_models=num_models,
            naming=SimpleNamespace(
                name_prefix="demo",
                include_feature_count_suffix=feature_suffix,
                include_constraint_count_suffix=constraint_suffix,
            ),
        )

        result = GeneratorWizardService.serialize_generated_model(
            feature_model,
            model,
            4,
        )

        assert result["filename"] == expected
        assert result["features"] == 3
        assert result["constraints"] == 1


def test_generate_sat_models_raises_after_twenty_failed_attempts(
    monkeypatch,
):
    class FakeModel:
        num_models = 1

    class FakeGeneratorModel:
        @staticmethod
        def from_flat_dict(params):
            return FakeModel()

    class FakeOperation:
        def execute(self, **kwargs):
            pass

        def get_result(self):
            return object()

    monkeypatch.setattr(wizard, "FmgeneratorModel", FakeGeneratorModel)
    monkeypatch.setattr(wizard, "GenerateFeatureModel", FakeOperation)
    monkeypatch.setattr(
        GeneratorWizardService,
        "is_satisfiable",
        staticmethod(lambda candidate: False),
    )

    with pytest.raises(
        wizard.SatisfiableModelGenerationError,
        match=r"No satisfiable model found for model 1 after 20 attempts",
    ):
        GeneratorWizardService.generate_sat_models({})
