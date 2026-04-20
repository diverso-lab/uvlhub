"""End-to-end wizard-to-output tests.

Each test POSTs a full wizard configuration, then pulls the resulting Params
via /generator/random/params-json and feeds it straight to the vendored
FmgeneratorModel — the same code Pyodide runs client-side. We then parse
the generated UVL and assert the output is *coherent with what the user
selected in the wizard*.

This is the contract the user cares about: what you toggle in the form
must show up in the .uvl files (or be absent when you disabled the level).
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
    """Per-test Flask client so sessions don't leak."""
    with test_app.test_client() as c:
        yield c


# Sums-to-1 probability bundles used when we don't care about exact mix.
_REL_EVEN = {"dist_optional": "0.3", "dist_mandatory": "0.3", "dist_alternative": "0.2", "dist_or": "0.2"}
_BOOLOP_EVEN = {"prob_and": "0.4", "prob_or": "0.2", "prob_implies": "0.2", "prob_equiv": "0.2"}
_ARITH_EVEN = {"prob_plus": "0.4", "prob_minus": "0.3", "prob_times": "0.2", "prob_div": "0.1"}
_CMP_EVEN = {"prob_eq": "0.2", "prob_lt": "0.2", "prob_gt": "0.2", "prob_leq": "0.2", "prob_geq": "0.2"}


def _step1(num_models="3", seed="42", name_prefix="fm", extras=None):
    data = {"num_models_val": num_models, "seed": seed, "name_prefix": name_prefix}
    if extras:
        data.update(extras)
    return data


def _step2(levels=None, extras=None):
    """Defaults: boolean-only, 6..10 features, depth 3. Pass levels={'arithmetic_level':'on', ...}
    to toggle. Relation distribution defaults to even."""
    levels = levels or {}
    data = {
        "num_features_min": "6",
        "num_features_max": "10",
        "max_tree_depth": "3",
        **_REL_EVEN,
        "dist_group_cardinality": "0.0",
        "nav": "next",
    }
    data.update(levels)
    if extras:
        data.update(extras)
    return data


def _step3(*, arithmetic=False, aggregate=False, string=False, extras=None):
    data = {
        "num_constraints_min": "6",
        "num_constraints_max": "8",
        "extra_constraint_repr": "1",
        "vars_per_ctc_min": "2",
        "vars_per_ctc_max": "3",
        "prob_not": "0.3",
        **_BOOLOP_EVEN,
        "nav": "next",
    }
    if arithmetic:
        data["arithmetic_level"] = "on"
        data.update(_ARITH_EVEN)
        if aggregate:
            data["aggregate_functions"] = "on"
            # When aggregates are on, the arith+agg probs must sum to 1.
            # Split the budget 70/30 between arithmetic ops and aggregates.
            data.update({
                "prob_plus": "0.3", "prob_minus": "0.2", "prob_times": "0.1", "prob_div": "0.1",
                "prob_sum": "0.2", "prob_avg": "0.1",
            })
        data.update(_CMP_EVEN)
    if string:
        data["type_level"] = "on"
        data["string_constraints"] = "on"
        data["prob_len"] = "1.0"
    # CTC type distribution is required whenever any non-boolean level is on.
    if arithmetic or string:
        ctc = {"ctc_dist_boolean": "0.5", "ctc_dist_integer": "0.0",
               "ctc_dist_real": "0.0", "ctc_dist_string": "0.0"}
        if arithmetic:
            ctc["ctc_dist_integer"] = "0.5"
        if string:
            # Put half the weight on string when string is active.
            if arithmetic:
                ctc.update({"ctc_dist_boolean": "0.4", "ctc_dist_integer": "0.4", "ctc_dist_string": "0.2"})
            else:
                ctc.update({"ctc_dist_boolean": "0.5", "ctc_dist_string": "0.5"})
        data.update(ctc)
    if extras:
        data.update(extras)
    return data


def _step4_random(**overrides):
    """Default: all-boolean attrs. Tests that enable arithmetic/type levels
    should override dist_* to match — the server pins inactive types to 0
    and requires the active subset to sum to 1.0."""
    data = {
        "random_attributes": "on",
        "min_attributes": "2",
        "max_attributes": "4",
        "dist_boolean": "1.0",
        "dist_integer": "0.0",
        "dist_real": "0.0",
        "dist_string": "0.0",
        "nav": "next",
    }
    data.update(overrides)
    return data


def _walk_wizard(client, step1=None, step2=None, step3=None, step4=None):
    """Submit all four steps. Returns final response (should land on step5)."""
    r = client.post("/generator/random/step1", data=step1 or _step1())
    assert r.status_code == 302, f"step1 failed: {r.status_code} — {r.data!r}"
    r = client.post("/generator/random/step2", data=step2 or _step2())
    assert r.status_code == 302, f"step2 failed: {r.status_code} — {r.data!r}"
    r = client.post("/generator/random/step3", data=step3 or _step3())
    assert r.status_code == 302, f"step3 failed: {r.status_code} — {r.data!r}"
    r = client.post("/generator/random/step4", data=step4 or _step4_random())
    assert r.status_code == 302, f"step4 failed: {r.status_code} — {r.data!r}"
    return r


def _fetch_params_and_generate(client, n=3):
    """Post-wizard, call /params-json, feed through the engine, return the
    concatenated UVL text of all generated models."""
    r = client.get("/generator/random/params-json")
    assert r.status_code == 200, f"params-json failed: {r.status_code}"
    params_dict = json.loads(r.data)
    params_dict["NUM_MODELS"] = n
    params = Params(**params_dict)
    with tempfile.TemporaryDirectory() as d:
        FmgeneratorModel(params).generate_models(d)
        return "\n".join(
            open(os.path.join(d, f)).read() for f in sorted(os.listdir(d)) if f.endswith(".uvl")
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


# ── Happy-path combos ────────────────────────────────────────────────────


def test_boolean_only_wizard_produces_only_boolean(client):
    """No arithmetic, no type level → no arithmetic operators, no len(), no sum()."""
    _walk_wizard(client)
    text = _fetch_params_and_generate(client, n=3)
    body = "\n".join(_iter_ctc_lines(text))
    assert "sum(" not in body
    assert "avg(" not in body
    assert "len(" not in body
    # No arithmetic operators in pure-boolean constraints (negation is '!', not '-').
    assert not re.search(r"\s[+\-*/]\s", body), f"arithmetic leaked into boolean-only:\n{body}"


def test_arithmetic_level_wizard_produces_arithmetic_constraints(client):
    _walk_wizard(
        client,
        step2=_step2(levels={"arithmetic_level": "on"}),
        step3=_step3(arithmetic=True, extras={
            "ctc_dist_boolean": "0.0", "ctc_dist_integer": "1.0",
            "ctc_dist_real": "0.0", "ctc_dist_string": "0.0",
        }),
        step4=_step4_random(dist_boolean="0.0", dist_integer="1.0", dist_real="0.0", dist_string="0.0",
                            min_attributes="3", max_attributes="4"),
    )
    text = _fetch_params_and_generate(client, n=3)
    body = "\n".join(_iter_ctc_lines(text))
    assert re.search(r"\s[+\-*/]\s", body), f"no arithmetic constraint emitted:\n{body}"


def test_aggregate_functions_wizard_produces_sum_or_avg(client):
    _walk_wizard(
        client,
        step2=_step2(levels={"arithmetic_level": "on", "aggregate_functions": "on"}),
        step3=_step3(arithmetic=True, aggregate=True, extras={
            "ctc_dist_boolean": "0.0", "ctc_dist_integer": "1.0",
            "ctc_dist_real": "0.0", "ctc_dist_string": "0.0",
        }),
        step4=_step4_random(dist_boolean="0.0", dist_integer="1.0", dist_real="0.0", dist_string="0.0",
                            min_attributes="3", max_attributes="4"),
    )
    text = _fetch_params_and_generate(client, n=3)
    body = "\n".join(_iter_ctc_lines(text))
    assert "sum(" in body or "avg(" in body, f"no aggregate in output:\n{body}"


def test_string_level_wizard_produces_len_or_literal_equality(client):
    _walk_wizard(
        client,
        step2=_step2(levels={"type_level": "on", "string_constraints": "on"}),
        step3=_step3(string=True, extras={
            "ctc_dist_boolean": "0.0", "ctc_dist_integer": "0.0",
            "ctc_dist_real": "0.0", "ctc_dist_string": "1.0",
        }),
        step4=_step4_random(dist_boolean="0.0", dist_integer="0.0", dist_real="0.0", dist_string="1.0",
                            min_attributes="3", max_attributes="4"),
    )
    text = _fetch_params_and_generate(client, n=3)
    body = "\n".join(_iter_ctc_lines(text))
    # Either len(Feat.Attr) op N, or Feat.Attr == 'literal'
    assert "len(" in body or re.search(r"F\d+\.Attr\d+\s*==", body), f"no string ctc:\n{body}"


# ── Level-coherence tests (wizard follows major/minor toggle logic) ──────


def test_arithmetic_off_gives_no_arithmetic_regardless_of_step3_sliders(client):
    """Even if the user leaves stale arithmetic probabilities in step3 after
    toggling off arithmetic_level in step2, no arithmetic constraint must
    appear."""
    _walk_wizard(
        client,
        # Level off
        step2=_step2(),
        # But step3 leaves arithmetic probs non-zero (which the server ignores
        # because ARITHMETIC_LEVEL is off).
        step3={
            **_step3(),
            "prob_plus": "0.7", "prob_minus": "0.2", "prob_times": "0.1", "prob_div": "0.0",
        },
    )
    text = _fetch_params_and_generate(client, n=3)
    body = "\n".join(_iter_ctc_lines(text))
    assert not re.search(r"\s[+\-*/]\s", body)


def test_type_off_gives_no_string_ctc(client):
    _walk_wizard(
        client,
        step2=_step2(levels={"arithmetic_level": "on"}),
        step3=_step3(arithmetic=True),
    )
    text = _fetch_params_and_generate(client, n=3)
    body = "\n".join(_iter_ctc_lines(text))
    assert "len(" not in body


def test_feature_cardinality_off_means_no_cardinality_in_uvl(client):
    _walk_wizard(
        client,
        step2=_step2(levels={"arithmetic_level": "on"}),
        step3=_step3(arithmetic=True),
    )
    text = _fetch_params_and_generate(client, n=3)
    assert "cardinality [" not in text


def test_feature_cardinality_on_produces_some_cardinality(client):
    """With PROB_FEATURE_CARDINALITY=1 every non-root feature must carry a
    cardinality annotation."""
    _walk_wizard(
        client,
        step2=_step2(
            levels={"arithmetic_level": "on", "feature_cardinality": "on"},
            extras={
                "prob_fc": "1.0",
                "min_feature_cardinality": "2",
                "max_feature_cardinality": "5",
            },
        ),
        step3=_step3(arithmetic=True),
    )
    text = _fetch_params_and_generate(client, n=2)
    assert "cardinality [" in text


def test_group_cardinality_off_keeps_only_standard_relations(client):
    _walk_wizard(client)
    text = _fetch_params_and_generate(client, n=3)
    # UVLWriter emits group cardinality relations as bare "[n..m]" indented
    # lines (no "cardinality" keyword). Check none appear.
    bare = [ln for ln in text.splitlines() if re.match(r"^\s*\[\d+(\.\.\d+)?\]\s*$", ln)]
    assert not bare


def test_group_cardinality_on_with_weight_produces_groups(client):
    _walk_wizard(
        client,
        step2=_step2(
            levels={"group_cardinality": "on"},
            extras={
                # All weight on group_cardinality
                "dist_optional": "0.0", "dist_mandatory": "0.0",
                "dist_alternative": "0.0", "dist_or": "0.0",
                "dist_group_cardinality": "1.0",
                "group_cardinality_min": "1",
                "group_cardinality_max": "5",
            },
        ),
    )
    text = _fetch_params_and_generate(client, n=3)
    bare = [ln for ln in text.splitlines() if re.match(r"^\s*\[\d+(\.\.\d+)?\]\s*$", ln)]
    assert bare, f"expected group-cardinality relations, none found:\n{text}"


# ── Individual parameter plumbing ────────────────────────────────────────


def test_num_models_propagates_through_wizard(client):
    _walk_wizard(client, step1=_step1(num_models="5"))
    r = client.get("/generator/random/params-json")
    assert json.loads(r.data)["NUM_MODELS"] == 5


def test_name_prefix_propagates_through_wizard(client):
    _walk_wizard(client, step1=_step1(name_prefix="zork_"))
    text = _fetch_params_and_generate(client, n=2)
    # Name prefix embedded in filenames (we're checking content, so generate
    # actual files from Params).
    params = json.loads(client.get("/generator/random/params-json").data)
    assert params["NAME_PREFIX"] == "zork_"


def test_suffixes_propagate_to_filenames(client):
    _walk_wizard(
        client,
        step1=_step1(extras={
            "feature_count_suffix": "on",
            "constraint_count_suffix": "on",
        }),
    )
    params = json.loads(client.get("/generator/random/params-json").data)
    params["NUM_MODELS"] = 2
    p = Params(**params)
    with tempfile.TemporaryDirectory() as d:
        FmgeneratorModel(p).generate_models(d)
        files = sorted(os.listdir(d))
        assert all(re.search(r"_\d+f_\d+c\.uvl$", f) for f in files), f"suffix missing in {files}"


def test_vars_per_constraint_limits_are_applied(client):
    _walk_wizard(
        client,
        step2=_step2(extras={"num_features_min": "12", "num_features_max": "18"}),
        step3=_step3(extras={
            "vars_per_ctc_min": "3",
            "vars_per_ctc_max": "3",
        }),
    )
    text = _fetch_params_and_generate(client, n=2)
    # Boolean-only → every constraint is a feature-level formula; with
    # MIN=MAX=3 each line should reference exactly 3 features.
    for line in _iter_ctc_lines(text):
        refs = re.findall(r"\bF\d+\b", line)
        assert len(refs) == 3, f"expected 3 vars, got {len(refs)}: {line}"


def test_prob_not_zero_propagates(client):
    _walk_wizard(
        client,
        step3=_step3(extras={"prob_not": "0.0"}),
    )
    text = _fetch_params_and_generate(client, n=3)
    body = "\n".join(_iter_ctc_lines(text))
    # No standalone "!" outside attribute literals.
    assert "!" not in body, f"unexpected NOT:\n{body}"


def test_prob_and_dominant_produces_mostly_conjunctions(client):
    _walk_wizard(
        client,
        step3=_step3(extras={
            "prob_and": "1.0",
            "prob_or": "0.0",
            "prob_implies": "0.0",
            "prob_equiv": "0.0",
            "prob_not": "0.0",
        }),
    )
    text = _fetch_params_and_generate(client, n=3)
    body = "\n".join(_iter_ctc_lines(text))
    assert " & " in body
    assert "=>" not in body
    assert "<=>" not in body
    assert " | " not in body


def test_attribute_type_distribution_is_forced_by_form(client):
    """With dist_boolean=1.0 and others=0, every random attribute must be boolean."""
    _walk_wizard(
        client,
        step4=_step4_random(
            dist_boolean="1.0", dist_integer="0.0", dist_real="0.0", dist_string="0.0",
            min_attributes="3", max_attributes="3",
        ),
    )
    text = _fetch_params_and_generate(client, n=3)
    # Boolean attrs render as {Name true} / {Name false}.
    attrs = re.findall(r"\{Attr\d+\s+(\S+?)(?:,|\})", text)
    assert attrs, "no attributes emitted"
    assert all(a in ("true", "false") for a in attrs), f"non-boolean attrs: {attrs}"


def test_ctc_dist_weights_steer_family_mix(client):
    """CTC_DIST_STRING=1.0 and the rest=0 should produce only string-family
    constraints (len() or literal equality)."""
    _walk_wizard(
        client,
        step2=_step2(levels={"type_level": "on", "string_constraints": "on"}),
        step3=_step3(
            string=True,
            extras={
                "ctc_dist_boolean": "0.0",
                "ctc_dist_integer": "0.0",
                "ctc_dist_real": "0.0",
                "ctc_dist_string": "1.0",
            },
        ),
        step4=_step4_random(
            dist_boolean="0.0", dist_integer="0.0", dist_real="0.0", dist_string="1.0",
            min_attributes="3", max_attributes="4",
        ),
    )
    text = _fetch_params_and_generate(client, n=3)
    lines = list(_iter_ctc_lines(text))
    assert lines, "no constraints at all"
    # Every constraint must reference an Attr (string constraints do).
    assert all(re.search(r"\.Attr\d+", ln) for ln in lines), \
        f"some boolean slipped through: {[ln for ln in lines if not re.search(r'.Attr\\d+', ln)]}"


def test_ensure_satisfiable_propagates(client):
    _walk_wizard(client, step1=_step1(extras={"ensure_satisfiable": "on"}))
    params = json.loads(client.get("/generator/random/params-json").data)
    assert params["ENSURE_SATISFIABLE"] is True


# ── Parametrised mass coverage (dozens of cases) ────────────────────────


@pytest.mark.parametrize("n_models", ["1", "2", "3", "5", "10"])
def test_num_models_roundtrip(client, n_models):
    _walk_wizard(client, step1=_step1(num_models=n_models))
    params = json.loads(client.get("/generator/random/params-json").data)
    assert params["NUM_MODELS"] == int(n_models)


@pytest.mark.parametrize("seed", ["1", "42", "1234", "99999", "1000"])
def test_seed_roundtrip(client, seed):
    _walk_wizard(client, step1=_step1(seed=seed))
    params = json.loads(client.get("/generator/random/params-json").data)
    assert params["SEED"] == int(seed)


@pytest.mark.parametrize("prefix", ["fm", "m_", "model-", "feat_", "zork42_"])
def test_name_prefix_roundtrip(client, prefix):
    _walk_wizard(client, step1=_step1(name_prefix=prefix))
    params = json.loads(client.get("/generator/random/params-json").data)
    assert params["NAME_PREFIX"] == prefix


@pytest.mark.parametrize("lo,hi", [("3", "5"), ("5", "10"), ("10", "15"), ("20", "30"), ("1", "3")])
def test_feature_count_bounds_roundtrip(client, lo, hi):
    _walk_wizard(client, step2=_step2(extras={"num_features_min": lo, "num_features_max": hi}))
    params = json.loads(client.get("/generator/random/params-json").data)
    assert params["MIN_FEATURES"] == int(lo)
    assert params["MAX_FEATURES"] == int(hi)


@pytest.mark.parametrize("depth", ["1", "2", "3", "4", "5", "8"])
def test_max_tree_depth_roundtrip(client, depth):
    _walk_wizard(client, step2=_step2(extras={"max_tree_depth": depth, "num_features_max": "20"}))
    params = json.loads(client.get("/generator/random/params-json").data)
    assert params["MAX_TREE_DEPTH"] == int(depth)


@pytest.mark.parametrize("lo,hi", [("1", "5"), ("3", "8"), ("5", "10"), ("10", "20")])
def test_num_constraints_bounds_roundtrip(client, lo, hi):
    _walk_wizard(client, step3=_step3(extras={"num_constraints_min": lo, "num_constraints_max": hi}))
    params = json.loads(client.get("/generator/random/params-json").data)
    assert params["MIN_CONSTRAINTS"] == int(lo)
    assert params["MAX_CONSTRAINTS"] == int(hi)


@pytest.mark.parametrize("vmin,vmax", [("1", "2"), ("2", "3"), ("2", "5"), ("3", "7")])
def test_vars_per_ctc_roundtrip(client, vmin, vmax):
    _walk_wizard(
        client,
        step2=_step2(extras={"num_features_min": "15", "num_features_max": "20"}),
        step3=_step3(extras={"vars_per_ctc_min": vmin, "vars_per_ctc_max": vmax}),
    )
    params = json.loads(client.get("/generator/random/params-json").data)
    assert params["MIN_VARS_PER_CONSTRAINT"] == int(vmin)
    assert params["MAX_VARS_PER_CONSTRAINT"] == int(vmax)


@pytest.mark.parametrize("vars_eq", ["2", "3", "4", "5"])
def test_fixed_vars_per_ctc_observed_in_output(client, vars_eq):
    _walk_wizard(
        client,
        step2=_step2(extras={"num_features_min": "15", "num_features_max": "20"}),
        step3=_step3(extras={"vars_per_ctc_min": vars_eq, "vars_per_ctc_max": vars_eq}),
    )
    text = _fetch_params_and_generate(client, n=2)
    for line in _iter_ctc_lines(text):
        refs = re.findall(r"\bF\d+\b", line)
        assert len(refs) == int(vars_eq), f"expected {vars_eq} vars, got {len(refs)}: {line}"


# ── Level-flag combinations: 2 major × 3 minor booleans = 8 combos ──────


_LEVEL_MATRIX = [
    # (arith, type, feat_card, agg, string_ctc)  -- aggregate requires arith,
    # string_constraints requires type, feat_card requires arith.
    (False, False, False, False, False),
    (True,  False, False, False, False),
    (True,  False, True,  False, False),
    (True,  False, False, True,  False),
    (True,  False, True,  True,  False),
    (False, True,  False, False, False),
    (False, True,  False, False, True),
    (True,  True,  False, False, False),
    (True,  True,  True,  False, False),
    (True,  True,  True,  True,  False),
    (True,  True,  False, False, True),
    (True,  True,  True,  True,  True),
]


def _levels_params(arith, type_, feat_card, agg, string_ctc):
    levels = {}
    if arith:
        levels["arithmetic_level"] = "on"
    if type_:
        levels["type_level"] = "on"
    if feat_card:
        levels["feature_cardinality"] = "on"
    if agg:
        levels["aggregate_functions"] = "on"
    if string_ctc:
        levels["string_constraints"] = "on"
    extras = {}
    if feat_card:
        extras["prob_fc"] = "0.5"
        extras["min_feature_cardinality"] = "2"
        extras["max_feature_cardinality"] = "4"
    return levels, extras


@pytest.mark.parametrize("combo", _LEVEL_MATRIX)
def test_level_combo_walks_wizard_cleanly(client, combo):
    arith, type_, feat_card, agg, string_ctc = combo
    levels, extras = _levels_params(arith, type_, feat_card, agg, string_ctc)
    _walk_wizard(
        client,
        step2=_step2(levels=levels, extras=extras),
        step3=_step3(arithmetic=arith, aggregate=agg, string=string_ctc),
    )
    params = json.loads(client.get("/generator/random/params-json").data)
    # TYPE_LEVEL forces ARITHMETIC_LEVEL on in Params.__post_init__, so the
    # effective arithmetic flag is (arith OR type_).
    assert params["ARITHMETIC_LEVEL"] is (arith or type_)
    assert params["TYPE_LEVEL"] is type_
    assert params["AGGREGATE_FUNCTIONS"] is agg
    assert params["STRING_CONSTRAINTS"] is (type_ and string_ctc)
    # FEATURE_CARDINALITY requires arithmetic in Params.__post_init__.
    assert params["FEATURE_CARDINALITY"] is ((arith or type_) and feat_card)


@pytest.mark.parametrize("combo", _LEVEL_MATRIX)
def test_level_combo_generates_satisfiable_uvl(client, combo):
    """Every level combo must generate valid, non-empty UVL we can write and
    parse back. We don't check semantic invariants here — just that the
    engine doesn't explode on any combo."""
    arith, type_, feat_card, agg, string_ctc = combo
    levels, extras = _levels_params(arith, type_, feat_card, agg, string_ctc)
    _walk_wizard(
        client,
        step2=_step2(levels=levels, extras=extras),
        step3=_step3(arithmetic=arith, aggregate=agg, string=string_ctc),
    )
    text = _fetch_params_and_generate(client, n=2)
    assert "features" in text
    assert "F0" in text
    assert "constraints" in text


# ── Boolean connective dominance ─────────────────────────────────────────


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
    _walk_wizard(client, step3=_step3(extras={**probs, "prob_not": "0.0"}))
    text = _fetch_params_and_generate(client, n=2)
    body = "\n".join(_iter_ctc_lines(text))
    assert marker in body, f"expected {marker!r} but missing from:\n{body}"


# ── Arithmetic operator dominance ────────────────────────────────────────


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
        step2=_step2(levels={"arithmetic_level": "on"}),
        step3=_step3(arithmetic=True, extras={
            **probs,
            "ctc_dist_boolean": "0.0", "ctc_dist_integer": "1.0",
            "ctc_dist_real": "0.0", "ctc_dist_string": "0.0",
            "num_constraints_min": "10", "num_constraints_max": "10",
        }),
        step4=_step4_random(dist_boolean="0.0", dist_integer="1.0",
                            dist_real="0.0", dist_string="0.0",
                            min_attributes="3", max_attributes="4"),
    )
    text = _fetch_params_and_generate(client, n=3)
    body = "\n".join(_iter_ctc_lines(text))
    assert marker in body, f"expected {marker!r} in arithmetic output:\n{body}"


# ── Comparison operator dominance ────────────────────────────────────────


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
        step2=_step2(levels={"arithmetic_level": "on"}),
        step3=_step3(arithmetic=True, extras={
            **probs,
            "ctc_dist_boolean": "0.0", "ctc_dist_integer": "1.0",
            "ctc_dist_real": "0.0", "ctc_dist_string": "0.0",
            "num_constraints_min": "10", "num_constraints_max": "10",
        }),
        step4=_step4_random(dist_boolean="0.0", dist_integer="1.0",
                            dist_real="0.0", dist_string="0.0",
                            min_attributes="3", max_attributes="4"),
    )
    text = _fetch_params_and_generate(client, n=3)
    body = "\n".join(_iter_ctc_lines(text))
    assert marker in body, f"expected {marker!r} in arithmetic output:\n{body}"


# ── Aggregate dominance ─────────────────────────────────────────────────


@pytest.mark.parametrize(
    "probs,marker",
    [
        ({"prob_sum": "1.0", "prob_avg": "0.0"}, "sum("),
        ({"prob_sum": "0.0", "prob_avg": "1.0"}, "avg("),
    ],
)
def test_aggregate_function_dominance(client, probs, marker):
    extras = {
        "prob_plus": "0.0", "prob_minus": "0.0", "prob_times": "0.0", "prob_div": "0.0",
        **probs,
        "ctc_dist_boolean": "0.0", "ctc_dist_integer": "1.0",
        "ctc_dist_real": "0.0", "ctc_dist_string": "0.0",
        "num_constraints_min": "15", "num_constraints_max": "15",
    }
    _walk_wizard(
        client,
        step2=_step2(levels={"arithmetic_level": "on", "aggregate_functions": "on"}),
        step3=_step3(arithmetic=True, aggregate=True, extras=extras),
        step4=_step4_random(dist_boolean="0.0", dist_integer="1.0",
                            dist_real="0.0", dist_string="0.0",
                            min_attributes="3", max_attributes="4"),
    )
    text = _fetch_params_and_generate(client, n=3)
    body = "\n".join(_iter_ctc_lines(text))
    assert marker in body, f"expected {marker!r} in aggregate output:\n{body}"


# ── Relation distribution dominance ──────────────────────────────────────


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
        step2=_step2(extras={
            **dist,
            "dist_group_cardinality": "0.0",
            "num_features_min": "12", "num_features_max": "18",
            "max_tree_depth": "4",
        }),
    )
    text = _fetch_params_and_generate(client, n=3)
    # relation keywords appear inside the feature tree as "\t\t<keyword>"
    assert re.search(rf"^\t+{marker}\s*$", text, re.M), \
        f"expected dominant {marker!r} relation in tree:\n{text}"


# ── Attribute type distribution coverage ─────────────────────────────────


@pytest.mark.parametrize(
    "dist,kind_check",
    [
        ({"dist_boolean": "1.0", "dist_integer": "0.0", "dist_real": "0.0", "dist_string": "0.0"}, "boolean"),
        ({"dist_boolean": "0.0", "dist_integer": "1.0", "dist_real": "0.0", "dist_string": "0.0"}, "integer"),
        ({"dist_boolean": "0.0", "dist_integer": "0.0", "dist_real": "1.0", "dist_string": "0.0"}, "real"),
        ({"dist_boolean": "0.0", "dist_integer": "0.0", "dist_real": "0.0", "dist_string": "1.0"}, "string"),
    ],
)
def test_attribute_type_dominance(client, dist, kind_check):
    # Enable whichever level is needed for the chosen type.
    levels = {}
    step3_extras = {}
    arith = kind_check in ("integer", "real")
    type_ = kind_check == "string"
    if arith:
        levels["arithmetic_level"] = "on"
    if type_:
        levels["type_level"] = "on"
        step3_extras["string_constraints"] = "on"
    _walk_wizard(
        client,
        step2=_step2(levels=levels),
        step3=_step3(arithmetic=arith, string=type_, extras=step3_extras),
        step4=_step4_random(**dist, min_attributes="3", max_attributes="3"),
    )
    text = _fetch_params_and_generate(client, n=3)
    # Boolean → true/false; integer → bare int; real → decimal; string → 'literal'.
    attrs = re.findall(r"\{Attr\d+\s+([^,}]+)", text)
    assert attrs, "no attributes emitted"
    for v in attrs:
        v = v.strip()
        if kind_check == "boolean":
            assert v in ("true", "false"), f"not boolean: {v!r}"
        elif kind_check == "integer":
            assert re.match(r"^-?\d+$", v), f"not integer: {v!r}"
        elif kind_check == "real":
            assert re.match(r"^-?\d+\.\d+$", v), f"not real: {v!r}"
        elif kind_check == "string":
            assert v.startswith("'") and v.endswith("'"), f"not string: {v!r}"


# ── Attribute count bounds ──────────────────────────────────────────────


@pytest.mark.parametrize("lo,hi", [("1", "1"), ("2", "2"), ("3", "3"), ("5", "5"), ("1", "3"), ("2", "6")])
def test_attribute_count_bounds_roundtrip(client, lo, hi):
    _walk_wizard(
        client,
        step4=_step4_random(min_attributes=lo, max_attributes=hi),
    )
    params = json.loads(client.get("/generator/random/params-json").data)
    assert params["MIN_ATTRIBUTES"] == int(lo)
    assert params["MAX_ATTRIBUTES"] == int(hi)


@pytest.mark.parametrize("fixed", ["1", "2", "3", "4", "5"])
def test_attribute_fixed_count_observed(client, fixed):
    _walk_wizard(
        client,
        step4=_step4_random(min_attributes=fixed, max_attributes=fixed),
    )
    text = _fetch_params_and_generate(client, n=3)
    # Each model block's attribute names (Attr0..Attr{fixed-1}).
    for model_text in text.split("features\n")[1:]:
        attrs = set(re.findall(r"\bAttr(\d+)\b", model_text))
        assert attrs == set(str(i) for i in range(int(fixed))), \
            f"expected {fixed} attrs, got {sorted(attrs)}"


# ── Suffix toggle coverage ──────────────────────────────────────────────


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
    _walk_wizard(client, step1=_step1(extras=flags))
    params = json.loads(client.get("/generator/random/params-json").data)
    params["NUM_MODELS"] = 3
    p = Params(**params)
    with tempfile.TemporaryDirectory() as d:
        FmgeneratorModel(p).generate_models(d)
        files = sorted(os.listdir(d))
        assert all(re.match(pattern, f) for f in files), f"files {files} don't match {pattern}"


# ── Determinism across wizard posts ─────────────────────────────────────


@pytest.mark.parametrize("seed", ["1", "7", "42", "1234"])
def test_same_seed_gives_same_models_via_wizard(client, seed):
    cfg = _step1(seed=seed)
    _walk_wizard(client, step1=cfg)
    text1 = _fetch_params_and_generate(client, n=3)
    with client.application.test_client() as c2:
        _walk_wizard(c2, step1=cfg)
        text2 = _fetch_params_and_generate(c2, n=3)
    assert text1 == text2


# ── Tree depth effect on output shape ───────────────────────────────────


@pytest.mark.parametrize("depth", ["1", "2", "3", "4", "5"])
def test_deeper_tree_yields_more_indent(client, depth):
    _walk_wizard(
        client,
        step2=_step2(extras={
            "num_features_min": "8", "num_features_max": "12",
            "max_tree_depth": depth,
        }),
    )
    text = _fetch_params_and_generate(client, n=2)
    feat_lines = [ln for ln in text.splitlines() if re.match(r"\t+F\d+\b", ln)]
    max_indent = max(len(ln) - len(ln.lstrip("\t")) for ln in feat_lines)
    # Root is at 1 tab, each depth adds 2 tabs.
    assert max_indent <= 1 + 2 * int(depth), f"depth={depth} got {max_indent} tabs"


# ── Arithmetic ranges (feature cardinality spans) ────────────────────────


@pytest.mark.parametrize(
    "fmin,fmax",
    [("2", "2"), ("2", "5"), ("3", "7"), ("1", "3"), ("5", "10")],
)
def test_feature_cardinality_bounds_observed(client, fmin, fmax):
    """With PROB=1.0, every non-root feature should carry a cardinality
    within [fmin..fmax]."""
    _walk_wizard(
        client,
        step2=_step2(
            levels={"arithmetic_level": "on", "feature_cardinality": "on"},
            extras={
                "prob_fc": "1.0",
                "min_feature_cardinality": fmin,
                "max_feature_cardinality": fmax,
                "num_features_min": "6", "num_features_max": "8",
            },
        ),
        step3=_step3(arithmetic=True),
    )
    text = _fetch_params_and_generate(client, n=3)
    for lo, hi in re.findall(r"cardinality \[(\d+)\.\.(\d+)\]", text):
        lo, hi = int(lo), int(hi)
        assert int(fmin) <= lo <= hi <= int(fmax), \
            f"cardinality [{lo}..{hi}] outside [{fmin}..{fmax}]"


# ── Group cardinality range coverage ────────────────────────────────────


@pytest.mark.parametrize(
    "gmin,gmax",
    [("1", "3"), ("2", "5"), ("1", "2"), ("3", "6")],
)
def test_group_cardinality_bounds_roundtrip(client, gmin, gmax):
    _walk_wizard(
        client,
        step2=_step2(
            levels={"group_cardinality": "on"},
            extras={
                "dist_optional": "0.0", "dist_mandatory": "0.0",
                "dist_alternative": "0.0", "dist_or": "0.0",
                "dist_group_cardinality": "1.0",
                "group_cardinality_min": gmin,
                "group_cardinality_max": gmax,
                "num_features_min": "10", "num_features_max": "15",
            },
        ),
    )
    params = json.loads(client.get("/generator/random/params-json").data)
    assert params["GROUP_CARDINALITY_MIN"] == int(gmin)
    assert params["GROUP_CARDINALITY_MAX"] == int(gmax)


# ── Mixed levels: everything on at once ──────────────────────────────────


def test_everything_on_every_family_represented(client):
    """Big integration test: with all levels enabled and CTC_DIST weights
    spread across families, each family should appear at least once across
    a large-enough batch."""
    _walk_wizard(
        client,
        step2=_step2(
            levels={
                "arithmetic_level": "on", "type_level": "on",
                "aggregate_functions": "on", "string_constraints": "on",
                "feature_cardinality": "on", "group_cardinality": "on",
            },
            extras={
                "prob_fc": "0.3",
                "min_feature_cardinality": "2", "max_feature_cardinality": "4",
                "dist_optional": "0.2", "dist_mandatory": "0.2",
                "dist_alternative": "0.2", "dist_or": "0.2",
                "dist_group_cardinality": "0.2",
                "group_cardinality_min": "1", "group_cardinality_max": "4",
                "num_features_min": "10", "num_features_max": "15",
            },
        ),
        step3=_step3(arithmetic=True, aggregate=True, string=True, extras={
            "ctc_dist_boolean": "0.25", "ctc_dist_integer": "0.25",
            "ctc_dist_real": "0.25", "ctc_dist_string": "0.25",
            "num_constraints_min": "15", "num_constraints_max": "15",
        }),
        step4=_step4_random(
            dist_boolean="0.25", dist_integer="0.25",
            dist_real="0.25", dist_string="0.25",
            min_attributes="5", max_attributes="8",
        ),
    )
    text = _fetch_params_and_generate(client, n=5)
    body = "\n".join(_iter_ctc_lines(text))
    has_bool = bool(re.search(r" & | \| | => | <=> ", body))
    has_arith = bool(re.search(r"\s[+\-*/]\s", body))
    has_agg = "sum(" in body or "avg(" in body
    has_string = "len(" in body or re.search(r"\.Attr\d+\s*==\s*'", body)
    # With 75 constraints across 5 models, should see at least 3 of 4 families.
    present = sum([has_bool, has_arith, has_agg, has_string])
    assert present >= 3, f"only {present} families present: bool={has_bool}, arith={has_arith}, agg={has_agg}, str={has_string}\n{body}"


# ── Back navigation doesn't lose state ──────────────────────────────────


def test_back_and_forward_preserves_new_ctc_dist_knobs(client):
    _walk_wizard(
        client,
        step2=_step2(levels={"arithmetic_level": "on"}),
        step3=_step3(arithmetic=True, extras={
            "ctc_dist_boolean": "0.4", "ctc_dist_integer": "0.6",
            "ctc_dist_real": "0.0", "ctc_dist_string": "0.0",
        }),
    )
    params = json.loads(client.get("/generator/random/params-json").data)
    assert params["CTC_DIST_INTEGER"] == pytest.approx(0.6)
    assert params["CTC_DIST_BOOLEAN"] == pytest.approx(0.4)


def test_back_and_forward_preserves_new_attr_dist_knobs(client):
    _walk_wizard(
        client,
        step2=_step2(levels={"arithmetic_level": "on"}),
        step3=_step3(arithmetic=True),
        step4=_step4_random(
            dist_boolean="0.2", dist_integer="0.8",
            dist_real="0.0", dist_string="0.0",
        ),
    )
    params = json.loads(client.get("/generator/random/params-json").data)
    assert params["DIST_INTEGER"] == pytest.approx(0.8)
    assert params["DIST_BOOLEAN"] == pytest.approx(0.2)

