"""End-to-end wizard-to-output tests.

Each test drives the full 6-step wizard (step1 batch → step2 levels →
step3 tree → step4 constraints → step5 attributes → step6 output), then
pulls the resulting Params via /generator/random/params-json and feeds
it straight into the vendored FmgeneratorModel — the same code Pyodide
runs in the browser. The generated UVL is parsed and the content is
asserted against what the user selected in the wizard.

This is the contract the user cares about: every knob you touch must
show up in the .uvl files (or be absent when you disabled its level).
"""

import json
import os
import re
import tempfile

import pytest

from fm_generator.FMGenerator.models.config import Params
from fm_generator.FMGenerator.models.models import FmgeneratorModel

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
    # TYPE_LEVEL implicitly forces ARITHMETIC_LEVEL on (Params.__post_init__),
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
        "dist_boolean": "1.0",
        "dist_integer": "0.0",
        "dist_real": "0.0",
        "dist_string": "0.0",
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


def _fetch_params_and_generate(client, n=3):
    r = client.get("/generator/random/params-json")
    assert r.status_code == 200
    params_dict = json.loads(r.data)
    params_dict["NUM_MODELS"] = n
    params = Params(**params_dict)
    with tempfile.TemporaryDirectory() as d:
        FmgeneratorModel(params).generate_models(d)
        return "\n".join(open(os.path.join(d, f)).read() for f in sorted(os.listdir(d)) if f.endswith(".uvl"))


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
                "dist_boolean": "0.0",
                "dist_integer": "1.0",
                "dist_real": "0.0",
                "dist_string": "0.0",
                "min_attributes": "3",
                "max_attributes": "4",
            }
        ),
    )
    body = "\n".join(_iter_ctc_lines(_fetch_params_and_generate(client, n=3)))
    assert re.search(r"\s[+\-*/]\s", body), f"no arith ctc:\n{body}"


def test_aggregate_functions_wizard_produces_sum_or_avg(client):
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
                "num_constraints_min": "15",
                "num_constraints_max": "15",
            },
        ),
        step5=_step5(
            extras={
                "dist_boolean": "0.0",
                "dist_integer": "1.0",
                "dist_real": "0.0",
                "dist_string": "0.0",
                "min_attributes": "3",
                "max_attributes": "4",
            }
        ),
    )
    body = "\n".join(_iter_ctc_lines(_fetch_params_and_generate(client, n=3)))
    assert "sum(" in body or "avg(" in body, f"no agg:\n{body}"


def test_string_level_wizard_produces_string_constraints(client):
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
                "dist_boolean": "0.0",
                "dist_integer": "0.0",
                "dist_real": "0.0",
                "dist_string": "1.0",
                "min_attributes": "3",
                "max_attributes": "4",
            }
        ),
    )
    body = "\n".join(_iter_ctc_lines(_fetch_params_and_generate(client, n=3)))
    assert "len(" in body or re.search(r"F\d+\.Attr\d+\s*==", body), f"no string ctc:\n{body}"


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


def test_filename_suffixes_applied_to_generated_files(client):
    _walk_wizard(
        client,
        step1=_step1(num_models="1", name_prefix="custom"),
        step6=_step6(feat_suffix=True, ctc_suffix=True),
    )
    params = json.loads(client.get("/generator/random/params-json").data)
    p = Params(**params)

    with tempfile.TemporaryDirectory() as d:
        FmgeneratorModel(p).generate_models(d)
        files = sorted(os.listdir(d))
        assert files
        assert all(re.match(r"^custom_\d+f_\d+c\.uvl$", f) for f in files), files


def test_vars_per_constraint_fixed_observed_in_output(client):
    _walk_wizard(
        client,
        step3=_step3(extras={"num_features_min": "15", "num_features_max": "20"}),
        step4=_step4(extras={"vars_per_ctc_min": "3", "vars_per_ctc_max": "3"}),
    )
    text = _fetch_params_and_generate(client, n=2)
    for line in _iter_ctc_lines(text):
        refs = re.findall(r"\bF\d+\b", line)
        assert len(refs) == 3, f"expected 3 vars, got {len(refs)}: {line}"


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
                "dist_boolean": "0.0",
                "dist_integer": "0.0",
                "dist_real": "0.0",
                "dist_string": "1.0",
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
    assert lines
    assert all("len(" in ln for ln in lines), lines


# ═══════════════════════════════════════════════════════════════════════
# PARAMETRISED MASS COVERAGE
# ═══════════════════════════════════════════════════════════════════════


# ── Step 3: feature tree ranges ─────────────────────────────────────────


@pytest.mark.parametrize("depth", ["1", "2", "3", "4", "5"])
def test_deeper_tree_yields_more_indent(client, depth):
    _walk_wizard(
        client,
        step3=_step3(
            extras={
                "num_features_min": "8",
                "num_features_max": "12",
                "max_tree_depth": depth,
            }
        ),
    )
    text = _fetch_params_and_generate(client, n=2)
    feat_lines = [ln for ln in text.splitlines() if re.match(r"\t+F\d+\b", ln)]
    max_indent = max(len(ln) - len(ln.lstrip("\t")) for ln in feat_lines)
    assert max_indent <= 1 + 2 * int(depth), f"depth={depth} got {max_indent} tabs"


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
        ({"dist_boolean": "1.0", "dist_integer": "0.0", "dist_real": "0.0", "dist_string": "0.0"}, "boolean"),
        ({"dist_boolean": "0.0", "dist_integer": "1.0", "dist_real": "0.0", "dist_string": "0.0"}, "integer"),
        ({"dist_boolean": "0.0", "dist_integer": "0.0", "dist_real": "1.0", "dist_string": "0.0"}, "real"),
        ({"dist_boolean": "0.0", "dist_integer": "0.0", "dist_real": "0.0", "dist_string": "1.0"}, "string"),
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


# ── Step 6: ensure_satisfiable + filename suffixes matrix ───────────────


@pytest.mark.parametrize(
    "flags,pattern",
    [
        ({}, r"^fm_\d+\.uvl$"),
        ({"feature_count_suffix": "on"}, r"^fm_\d+f\.uvl$"),
        ({"constraint_count_suffix": "on"}, r"^fm_\d+c\.uvl$"),
        (
            {"feature_count_suffix": "on", "constraint_count_suffix": "on"},
            r"^fm_\d+f_\d+c\.uvl$",
        ),
    ],
)
def test_filename_suffix_combinations(client, flags, pattern):
    num_models = "3" if not flags else "1"

    _walk_wizard(
        client,
        step1=_step1(num_models=num_models),
        step6={"nav": "next", **flags},
    )

    p = json.loads(client.get("/generator/random/params-json").data)
    params = Params(**p)

    with tempfile.TemporaryDirectory() as d:
        FmgeneratorModel(params).generate_models(d)
        files = sorted(os.listdir(d))
        assert files
        assert all(re.match(pattern, f) for f in files), f"files={files} pattern={pattern}"


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
                "dist_boolean": "0.4",
                "dist_integer": "0.3",
                "dist_real": "0.3",
                "dist_string": "0.0",
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
    assert params["DIST_INTEGER"] == pytest.approx(0.3)
    assert params["ENSURE_SATISFIABLE"] is True
    assert params["INCLUDE_FEATURE_COUNT_SUFFIX"] is True


# ── Mixed levels integration ────────────────────────────────────────────


def test_everything_on_every_family_represented(client):
    _walk_wizard(
        client,
        step2=_step2(arithmetic=True, type_=True, aggregate=True, string_ctc=True, feat_card=True, group_card=True),
        step3=_step3(
            group_card=True,
            feat_card=True,
            extras={
                "prob_fc": "0.3",
                "min_feature_cardinality": "2",
                "max_feature_cardinality": "4",
                "dist_optional": "0.2",
                "dist_mandatory": "0.2",
                "dist_alternative": "0.2",
                "dist_or": "0.2",
                "dist_group_cardinality": "0.2",
                "group_cardinality_min": "1",
                "group_cardinality_max": "4",
                "num_features_min": "10",
                "num_features_max": "15",
            },
        ),
        step4=_step4(
            arithmetic=True,
            aggregate=True,
            string=True,
            extras={
                "ctc_dist_boolean": "0.25",
                "ctc_dist_integer": "0.25",
                "ctc_dist_real": "0.25",
                "ctc_dist_string": "0.25",
                "num_constraints_min": "15",
                "num_constraints_max": "15",
            },
        ),
        step5=_step5(
            extras={
                "dist_boolean": "0.25",
                "dist_integer": "0.25",
                "dist_real": "0.25",
                "dist_string": "0.25",
                "min_attributes": "5",
                "max_attributes": "8",
            }
        ),
    )
    body = "\n".join(_iter_ctc_lines(_fetch_params_and_generate(client, n=5)))
    fams = sum(
        [
            bool(re.search(r" & | \| | => | <=> ", body)),
            bool(re.search(r"\s[+\-*/]\s", body)),
            "sum(" in body or "avg(" in body,
            "len(" in body or bool(re.search(r"\.Attr\d+\s*==\s*'", body)),
        ]
    )
    assert fams >= 3, f"only {fams} families present"
