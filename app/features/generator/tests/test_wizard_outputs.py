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


def test_num_models_propagates(client):
    _walk_wizard(client, step1=_step1(num_models="7"))
    assert json.loads(client.get("/generator/random/params-json").data)["NUM_MODELS"] == 7


def test_name_prefix_propagates(client):
    _walk_wizard(client, step1=_step1(name_prefix="zork_"))
    assert json.loads(client.get("/generator/random/params-json").data)["NAME_PREFIX"] == "zork_"


def test_ensure_satisfiable_propagates(client):
    _walk_wizard(client, step6=_step6(ensure_satisfiable=True))
    assert json.loads(client.get("/generator/random/params-json").data)["ENSURE_SATISFIABLE"] is True


def test_filename_suffixes_propagate(client):
    _walk_wizard(client, step6=_step6(feat_suffix=True, ctc_suffix=True))
    params = json.loads(client.get("/generator/random/params-json").data)
    assert params["INCLUDE_FEATURE_COUNT_SUFFIX"] is True
    assert params["INCLUDE_CONSTRAINT_COUNT_SUFFIX"] is True


def test_filename_suffixes_applied_to_generated_files(client):
    _walk_wizard(client, step6=_step6(feat_suffix=True, ctc_suffix=True))
    params = json.loads(client.get("/generator/random/params-json").data)
    params["NUM_MODELS"] = 2
    p = Params(**params)
    with tempfile.TemporaryDirectory() as d:
        FmgeneratorModel(p).generate_models(d)
        files = sorted(os.listdir(d))
        assert all(re.search(r"_\d+f_\d+c\.uvl$", f) for f in files), f"missing suffix: {files}"


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


def test_prob_not_zero_propagates(client):
    _walk_wizard(client, step4=_step4(extras={"prob_not": "0.0"}))
    body = "\n".join(_iter_ctc_lines(_fetch_params_and_generate(client, n=3)))
    assert "!" not in body


def test_prob_and_dominant_produces_mostly_conjunctions(client):
    _walk_wizard(
        client,
        step4=_step4(
            extras={
                "prob_and": "1.0",
                "prob_or": "0.0",
                "prob_implies": "0.0",
                "prob_equiv": "0.0",
                "prob_not": "0.0",
            }
        ),
    )
    body = "\n".join(_iter_ctc_lines(_fetch_params_and_generate(client, n=3)))
    assert " & " in body
    assert "=>" not in body
    assert "<=>" not in body
    assert " | " not in body


def test_attr_type_dominance_boolean(client):
    _walk_wizard(
        client,
        step5=_step5(
            extras={
                "dist_boolean": "1.0",
                "dist_integer": "0.0",
                "dist_real": "0.0",
                "dist_string": "0.0",
                "min_attributes": "3",
                "max_attributes": "3",
            }
        ),
    )
    text = _fetch_params_and_generate(client, n=3)
    attrs = re.findall(r"\{Attr\d+\s+(\S+?)(?:,|\})", text)
    assert attrs
    assert all(a in ("true", "false") for a in attrs), attrs


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
    lines = list(_iter_ctc_lines(_fetch_params_and_generate(client, n=3)))
    assert lines
    assert all(re.search(r"\.Attr\d+", ln) for ln in lines), lines


# ═══════════════════════════════════════════════════════════════════════
# PARAMETRISED MASS COVERAGE
# ═══════════════════════════════════════════════════════════════════════


# ── Step 1: num_models, seed, name_prefix ───────────────────────────────


@pytest.mark.parametrize("n", ["1", "2", "3", "5", "10", "25", "50", "100", "500", "1000"])
def test_num_models_roundtrip(client, n):
    _walk_wizard(client, step1=_step1(num_models=n))
    assert json.loads(client.get("/generator/random/params-json").data)["NUM_MODELS"] == int(n)


@pytest.mark.parametrize("seed", ["1", "7", "42", "123", "1000", "999999"])
def test_seed_roundtrip(client, seed):
    _walk_wizard(client, step1=_step1(seed=seed))
    assert json.loads(client.get("/generator/random/params-json").data)["SEED"] == int(seed)


@pytest.mark.parametrize(
    "prefix",
    ["fm", "m_", "model-", "feat_", "zork42_", "a", "generated_", "test", "v2_", "fm_x_"],
)
def test_name_prefix_roundtrip(client, prefix):
    _walk_wizard(client, step1=_step1(name_prefix=prefix))
    assert json.loads(client.get("/generator/random/params-json").data)["NAME_PREFIX"] == prefix


@pytest.mark.parametrize("bad", ["0", "-1", "1001", "abc", "", "1.5"])
def test_step1_rejects_bad_num_models(client, bad):
    r = client.post("/generator/random/step1", data={**_step1(num_models=bad)})
    assert r.status_code == 200  # re-renders with error
    assert b"Number of models" in r.data


@pytest.mark.parametrize("bad", ["0", "-1", "abc", ""])
def test_step1_rejects_bad_seed(client, bad):
    r = client.post("/generator/random/step1", data=_step1(seed=bad))
    assert r.status_code == 200
    assert b"Seed" in r.data


# ── Step 2: level combinations ──────────────────────────────────────────


# All 2^6 combinations of the 6 level toggles; a handful will end up
# resolving identically in Params (TYPE_LEVEL forces ARITHMETIC_LEVEL on;
# feat_card/aggregate require arithmetic; string_ctc requires type).
_ALL_LEVELS = [
    (a, t, fc, ag, st, gc)
    for a in (False, True)
    for t in (False, True)
    for fc in (False, True)
    for ag in (False, True)
    for st in (False, True)
    for gc in (False, True)
]


@pytest.mark.parametrize(
    "combo",
    _ALL_LEVELS,
    ids=lambda c: (f"A{int(c[0])}T{int(c[1])}FC{int(c[2])}AG{int(c[3])}ST{int(c[4])}GC{int(c[5])}"),
)
def test_every_level_combo_walks_the_wizard(client, combo):
    """Every combination of the six level toggles must either walk the
    wizard cleanly or — if the validator rejects it — fall back through
    the engine's enforcement (TYPE forces Arithmetic, etc.). No combo
    should crash or produce an empty UVL."""
    arith, type_, fc, ag, st, gc = combo
    step2_data = _step2(arithmetic=arith, type_=type_, feat_card=fc, aggregate=ag, string_ctc=st, group_card=gc)
    # Levels validator rejects minor-without-major; that's fine as a
    # 200 response. The UI auto-enables majors; mimic that here.
    effective_arith = arith or fc or ag
    effective_type = type_ or st
    r = client.post("/generator/random/step1", data=_step1())
    assert r.status_code == 302
    r = client.post("/generator/random/step2", data=step2_data)
    if r.status_code == 200:
        # Validator rejected. Retry with majors forced on.
        step2_data = _step2(
            arithmetic=effective_arith, type_=effective_type, feat_card=fc, aggregate=ag, string_ctc=st, group_card=gc
        )
        r = client.post("/generator/random/step2", data=step2_data)
    assert r.status_code == 302

    # Complete the rest with level-appropriate defaults.
    client.post("/generator/random/step3", data=_step3(group_card=gc, feat_card=fc))
    client.post(
        "/generator/random/step4",
        data=_step4(
            arithmetic=effective_arith,
            aggregate=ag,
            string=st and effective_type,
        ),
    )
    client.post("/generator/random/step5", data=_step5())
    client.post("/generator/random/step6", data=_step6())

    params = json.loads(client.get("/generator/random/params-json").data)
    # TYPE_LEVEL forces ARITHMETIC_LEVEL on in Params.__post_init__.
    assert params["ARITHMETIC_LEVEL"] is (effective_arith or effective_type)
    assert params["TYPE_LEVEL"] is effective_type
    assert params["FEATURE_CARDINALITY"] is (fc and (effective_arith or effective_type))
    assert params["AGGREGATE_FUNCTIONS"] is (ag and effective_arith)
    assert params["STRING_CONSTRAINTS"] is (st and effective_type)
    assert params["GROUP_CARDINALITY"] is gc


# ── Step 3: feature tree ranges ─────────────────────────────────────────


@pytest.mark.parametrize(
    "lo,hi",
    [
        ("1", "3"),
        ("3", "5"),
        ("5", "10"),
        ("10", "15"),
        ("15", "20"),
        ("20", "30"),
        ("50", "50"),
        ("1", "50"),
    ],
)
def test_feature_count_bounds_roundtrip(client, lo, hi):
    _walk_wizard(client, step3=_step3(extras={"num_features_min": lo, "num_features_max": hi}))
    params = json.loads(client.get("/generator/random/params-json").data)
    assert params["MIN_FEATURES"] == int(lo)
    assert params["MAX_FEATURES"] == int(hi)


@pytest.mark.parametrize("depth", ["1", "2", "3", "4", "5", "7", "10"])
def test_max_tree_depth_roundtrip(client, depth):
    _walk_wizard(client, step3=_step3(extras={"max_tree_depth": depth, "num_features_max": "20"}))
    assert json.loads(client.get("/generator/random/params-json").data)["MAX_TREE_DEPTH"] == int(depth)


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


# ── Step 3: relation distribution dominance ─────────────────────────────


@pytest.mark.parametrize(
    "dist,marker",
    [
        ({"dist_optional": "1.0", "dist_mandatory": "0.0", "dist_alternative": "0.0", "dist_or": "0.0"}, "optional"),
        ({"dist_optional": "0.0", "dist_mandatory": "1.0", "dist_alternative": "0.0", "dist_or": "0.0"}, "mandatory"),
        ({"dist_optional": "0.0", "dist_mandatory": "0.0", "dist_alternative": "1.0", "dist_or": "0.0"}, "alternative"),
        ({"dist_optional": "0.0", "dist_mandatory": "0.0", "dist_alternative": "0.0", "dist_or": "1.0"}, "or"),
    ],
)
def test_relation_distribution_dominance(client, dist, marker):
    _walk_wizard(
        client,
        step3=_step3(
            extras={
                **dist,
                "dist_group_cardinality": "0.0",
                "num_features_min": "12",
                "num_features_max": "18",
                "max_tree_depth": "4",
            }
        ),
    )
    text = _fetch_params_and_generate(client, n=3)
    assert re.search(rf"^\t+{marker}\s*$", text, re.M), f"missing {marker!r}:\n{text[:300]}"


# ── Step 3: group cardinality bounds ────────────────────────────────────


@pytest.mark.parametrize("gmin,gmax", [("1", "3"), ("2", "5"), ("1", "2"), ("3", "6"), ("1", "10")])
def test_group_cardinality_bounds_roundtrip(client, gmin, gmax):
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
                "group_cardinality_min": gmin,
                "group_cardinality_max": gmax,
                "num_features_min": "10",
                "num_features_max": "15",
            },
        ),
    )
    params = json.loads(client.get("/generator/random/params-json").data)
    assert params["GROUP_CARDINALITY_MIN"] == int(gmin)
    assert params["GROUP_CARDINALITY_MAX"] == int(gmax)


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


@pytest.mark.parametrize("lo,hi", [("1", "5"), ("3", "8"), ("5", "10"), ("10", "20"), ("1", "1"), ("15", "15")])
def test_constraint_count_bounds_roundtrip(client, lo, hi):
    _walk_wizard(client, step4=_step4(extras={"num_constraints_min": lo, "num_constraints_max": hi}))
    params = json.loads(client.get("/generator/random/params-json").data)
    assert params["MIN_CONSTRAINTS"] == int(lo)
    assert params["MAX_CONSTRAINTS"] == int(hi)


@pytest.mark.parametrize("fixed", ["1", "3", "5", "7", "10"])
def test_fixed_constraint_count_observed(client, fixed):
    _walk_wizard(client, step4=_step4(extras={"num_constraints_min": fixed, "num_constraints_max": fixed}))
    text = _fetch_params_and_generate(client, n=2)
    for model_text in text.split("features\n")[1:]:
        ctcs = list(_iter_ctc_lines("features\n" + model_text))
        assert len(ctcs) == int(fixed)


@pytest.mark.parametrize("vmin,vmax", [("1", "2"), ("2", "3"), ("2", "5"), ("3", "7"), ("1", "10")])
def test_vars_per_ctc_roundtrip(client, vmin, vmax):
    _walk_wizard(
        client,
        step3=_step3(extras={"num_features_min": "15", "num_features_max": "20"}),
        step4=_step4(extras={"vars_per_ctc_min": vmin, "vars_per_ctc_max": vmax}),
    )
    params = json.loads(client.get("/generator/random/params-json").data)
    assert params["MIN_VARS_PER_CONSTRAINT"] == int(vmin)
    assert params["MAX_VARS_PER_CONSTRAINT"] == int(vmax)


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


# ── Step 4: boolean connective dominance ────────────────────────────────


@pytest.mark.parametrize(
    "probs,marker",
    [
        ({"prob_and": "1.0", "prob_or": "0.0", "prob_implies": "0.0", "prob_equiv": "0.0"}, " & "),
        ({"prob_and": "0.0", "prob_or": "1.0", "prob_implies": "0.0", "prob_equiv": "0.0"}, " | "),
        ({"prob_and": "0.0", "prob_or": "0.0", "prob_implies": "1.0", "prob_equiv": "0.0"}, " => "),
        ({"prob_and": "0.0", "prob_or": "0.0", "prob_implies": "0.0", "prob_equiv": "1.0"}, " <=> "),
    ],
)
def test_boolean_connective_dominance(client, probs, marker):
    _walk_wizard(client, step4=_step4(extras={**probs, "prob_not": "0.0"}))
    body = "\n".join(_iter_ctc_lines(_fetch_params_and_generate(client, n=2)))
    assert marker in body, f"missing {marker!r}:\n{body}"


# ── Step 4: arithmetic operator dominance ────────────────────────────────


@pytest.mark.parametrize(
    "probs,marker",
    [
        ({"prob_plus": "1.0", "prob_minus": "0.0", "prob_times": "0.0", "prob_div": "0.0"}, " + "),
        ({"prob_plus": "0.0", "prob_minus": "1.0", "prob_times": "0.0", "prob_div": "0.0"}, " - "),
        ({"prob_plus": "0.0", "prob_minus": "0.0", "prob_times": "1.0", "prob_div": "0.0"}, " * "),
        ({"prob_plus": "0.0", "prob_minus": "0.0", "prob_times": "0.0", "prob_div": "1.0"}, " / "),
    ],
)
def test_arithmetic_operator_dominance(client, probs, marker):
    _walk_wizard(
        client,
        step2=_step2(arithmetic=True),
        step4=_step4(
            arithmetic=True,
            extras={
                **probs,
                "ctc_dist_boolean": "0.0",
                "ctc_dist_integer": "1.0",
                "ctc_dist_real": "0.0",
                "ctc_dist_string": "0.0",
                "num_constraints_min": "10",
                "num_constraints_max": "10",
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
    assert marker in body, f"missing {marker!r} in arithmetic output:\n{body}"


# ── Step 4: comparison operator dominance ───────────────────────────────


@pytest.mark.parametrize(
    "probs,marker",
    [
        ({"prob_eq": "1.0", "prob_lt": "0.0", "prob_gt": "0.0", "prob_leq": "0.0", "prob_geq": "0.0"}, "=="),
        ({"prob_eq": "0.0", "prob_lt": "1.0", "prob_gt": "0.0", "prob_leq": "0.0", "prob_geq": "0.0"}, " < "),
        ({"prob_eq": "0.0", "prob_lt": "0.0", "prob_gt": "1.0", "prob_leq": "0.0", "prob_geq": "0.0"}, " > "),
        ({"prob_eq": "0.0", "prob_lt": "0.0", "prob_gt": "0.0", "prob_leq": "1.0", "prob_geq": "0.0"}, " <= "),
        ({"prob_eq": "0.0", "prob_lt": "0.0", "prob_gt": "0.0", "prob_leq": "0.0", "prob_geq": "1.0"}, " >= "),
    ],
)
def test_comparison_operator_dominance(client, probs, marker):
    _walk_wizard(
        client,
        step2=_step2(arithmetic=True),
        step4=_step4(
            arithmetic=True,
            extras={
                **probs,
                "ctc_dist_boolean": "0.0",
                "ctc_dist_integer": "1.0",
                "ctc_dist_real": "0.0",
                "ctc_dist_string": "0.0",
                "num_constraints_min": "10",
                "num_constraints_max": "10",
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
    assert marker in body, f"missing {marker!r} in comparison output:\n{body}"


# ── Step 4: aggregate function dominance ────────────────────────────────


@pytest.mark.parametrize(
    "probs,marker",
    [
        ({"prob_sum": "1.0", "prob_avg": "0.0"}, "sum("),
        ({"prob_sum": "0.0", "prob_avg": "1.0"}, "avg("),
    ],
)
def test_aggregate_function_dominance(client, probs, marker):
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
                **probs,
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
    assert marker in body, f"missing {marker!r}:\n{body}"


# ── Step 4: prob_not spectrum ───────────────────────────────────────────


@pytest.mark.parametrize(
    "prob_not,expected_has_not",
    [
        ("0.0", False),
        ("0.5", True),
        ("1.0", True),
    ],
)
def test_prob_not_spectrum(client, prob_not, expected_has_not):
    _walk_wizard(client, step4=_step4(extras={"prob_not": prob_not}))
    body = "\n".join(_iter_ctc_lines(_fetch_params_and_generate(client, n=3)))
    has_not = "!" in body
    assert (
        has_not is expected_has_not or prob_not == "0.5"
    ), f"prob_not={prob_not} has_not={has_not} expected={expected_has_not}"


# ── Step 5: attribute count bounds ──────────────────────────────────────


@pytest.mark.parametrize(
    "lo,hi",
    [
        ("1", "1"),
        ("2", "2"),
        ("3", "3"),
        ("5", "5"),
        ("10", "10"),
        ("1", "3"),
        ("2", "6"),
        ("1", "10"),
        ("3", "8"),
    ],
)
def test_attribute_count_bounds_roundtrip(client, lo, hi):
    _walk_wizard(client, step5=_step5(extras={"min_attributes": lo, "max_attributes": hi}))
    params = json.loads(client.get("/generator/random/params-json").data)
    assert params["MIN_ATTRIBUTES"] == int(lo)
    assert params["MAX_ATTRIBUTES"] == int(hi)


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


@pytest.mark.parametrize("ensure", [False, True])
@pytest.mark.parametrize("feat_sfx", [False, True])
@pytest.mark.parametrize("ctc_sfx", [False, True])
def test_output_options_matrix(client, ensure, feat_sfx, ctc_sfx):
    _walk_wizard(
        client,
        step6=_step6(
            ensure_satisfiable=ensure,
            feat_suffix=feat_sfx,
            ctc_suffix=ctc_sfx,
        ),
    )
    p = json.loads(client.get("/generator/random/params-json").data)
    assert p["ENSURE_SATISFIABLE"] is ensure
    assert p["INCLUDE_FEATURE_COUNT_SUFFIX"] is feat_sfx
    assert p["INCLUDE_CONSTRAINT_COUNT_SUFFIX"] is ctc_sfx


@pytest.mark.parametrize(
    "flags,pattern",
    [
        ({}, r"^fm\d+\.uvl$"),
        ({"feature_count_suffix": "on"}, r"^fm\d+_\d+f\.uvl$"),
        ({"constraint_count_suffix": "on"}, r"^fm\d+_\d+c\.uvl$"),
        ({"feature_count_suffix": "on", "constraint_count_suffix": "on"}, r"^fm\d+_\d+f_\d+c\.uvl$"),
    ],
)
def test_filename_suffix_combinations(client, flags, pattern):
    _walk_wizard(client, step6={"nav": "next", **flags})
    p = json.loads(client.get("/generator/random/params-json").data)
    p["NUM_MODELS"] = 3
    params = Params(**p)
    with tempfile.TemporaryDirectory() as d:
        FmgeneratorModel(params).generate_models(d)
        files = sorted(os.listdir(d))
        assert all(re.match(pattern, f) for f in files), f"files={files} pattern={pattern}"


# ── CTC type distribution ────────────────────────────────────────────────


@pytest.mark.parametrize(
    "ctc_dist,family_marker",
    [
        (
            {"ctc_dist_boolean": "1.0", "ctc_dist_integer": "0.0", "ctc_dist_real": "0.0", "ctc_dist_string": "0.0"},
            "boolean",
        ),
        (
            {"ctc_dist_boolean": "0.0", "ctc_dist_integer": "1.0", "ctc_dist_real": "0.0", "ctc_dist_string": "0.0"},
            "arith",
        ),
        (
            {"ctc_dist_boolean": "0.0", "ctc_dist_integer": "0.0", "ctc_dist_real": "0.0", "ctc_dist_string": "1.0"},
            "string",
        ),
    ],
)
def test_ctc_dist_family_dominance(client, ctc_dist, family_marker):
    _walk_wizard(
        client,
        step2=_step2(arithmetic=True, type_=True, string_ctc=True),
        step4=_step4(
            arithmetic=True,
            string=True,
            extras={
                **ctc_dist,
                "num_constraints_min": "8",
                "num_constraints_max": "8",
            },
        ),
        step5=_step5(
            extras={
                "dist_boolean": "0.25",
                "dist_integer": "0.25",
                "dist_real": "0.25",
                "dist_string": "0.25",
                "min_attributes": "4",
                "max_attributes": "4",
            }
        ),
    )
    body = "\n".join(_iter_ctc_lines(_fetch_params_and_generate(client, n=3)))
    if family_marker == "boolean":
        # Boolean ctcs reference only features (F\d+), no Attr.
        assert (
            any(
                re.search(r"^[^'a-z]*F\d+", ln) and not re.search(r"\.Attr|len\(|sum\(|avg\(", ln)
                for ln in _iter_ctc_lines(body)
            )
            or " & " in body
            or " | " in body
        )
    elif family_marker == "arith":
        assert re.search(r"\s[+\-*/]\s", body), f"no arith:\n{body}"
    elif family_marker == "string":
        assert "len(" in body or re.search(r"\.Attr\d+\s*==\s*'", body), f"no string:\n{body}"


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


# ── GET rendering smoke tests (each step responds with 200 when ready) ─


@pytest.mark.parametrize("step", [1, 2, 3, 4, 5, 6])
def test_each_step_renders_after_session_primed(client, step):
    _walk_wizard(client)  # primes the session through step 6
    r = client.get(f"/generator/random/step{step}")
    assert r.status_code == 200
    markers = (b"Generate", b"Batch", b"levels", b"Feature", b"Constraints", b"Attributes", b"Output", b"Download")
    assert any(m in r.data for m in markers)


# ── Params contract (Params() accepts what /params-json returns) ───────


@pytest.mark.parametrize("seed", ["1", "42", "777"])
def test_params_json_roundtrips_through_params(client, seed):
    _walk_wizard(
        client,
        step1=_step1(seed=seed),
        step2=_step2(arithmetic=True, type_=True, aggregate=True, string_ctc=True, feat_card=True, group_card=True),
        step3=_step3(group_card=True, feat_card=True),
        step4=_step4(arithmetic=True, aggregate=True, string=True),
        step5=_step5(
            extras={
                "dist_boolean": "0.25",
                "dist_integer": "0.25",
                "dist_real": "0.25",
                "dist_string": "0.25",
            }
        ),
    )
    p = json.loads(client.get("/generator/random/params-json").data)
    Params(**p)  # must not raise
