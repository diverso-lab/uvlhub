"""End-to-end wizard tests driven through Flask's test client.

The wizard is 6 steps:
    1 Batch → 2 Levels → 3 Tree → 4 Constraints → 5 Attributes → 6 Output.

Each step has its own URL (``/generator/random/stepN``) and only persists
the fields it owns. These tests exercise the happy path and the regression
scenarios we've already fixed.
"""

import json

import pytest

from fm_generator.FMGenerator.models.config import Params

# Minimum valid payloads, coherent with each step's validator.
STEP1 = {"num_models_val": "3", "seed": "42", "name_prefix": "fm"}
STEP2 = {}  # pure-Boolean (no levels toggled)
STEP3 = {
    "num_features_min": "5",
    "num_features_max": "20",
    "max_tree_depth": "5",
    "dist_optional": "0.3",
    "dist_mandatory": "0.3",
    "dist_alternative": "0.2",
    "dist_or": "0.2",
    "nav": "next",
}
STEP4 = {
    "num_constraints_min": "1",
    "num_constraints_max": "5",
    "extra_constraint_repr": "1",
    "vars_per_ctc_min": "1",
    "vars_per_ctc_max": "3",
    "prob_not": "0.3",
    "prob_and": "0.4",
    "prob_or": "0.2",
    "prob_implies": "0.2",
    "prob_equiv": "0.2",
    "nav": "next",
}
STEP5 = {
    "random_attributes": "on",
    "min_attributes": "1",
    "max_attributes": "3",
    "dist_boolean": "1.0",
    "dist_integer": "0.0",
    "dist_real": "0.0",
    "dist_string": "0.0",
    "nav": "next",
}
STEP6 = {"nav": "next"}


@pytest.fixture
def client(test_app):
    with test_app.test_client() as c:
        yield c


def _walk_happy_path(client, step2=None, step3=None, step4=None, step5=None, step6=None):
    r = client.post("/generator/random/step1", data=STEP1)
    assert r.status_code == 302 and r.location.endswith("/step2"), (r.status_code, r.location)
    r = client.post("/generator/random/step2", data=step2 or STEP2)
    assert r.status_code == 302 and r.location.endswith("/step3"), (r.status_code, r.location)
    r = client.post("/generator/random/step3", data=step3 or STEP3)
    assert r.status_code == 302 and r.location.endswith("/step4"), (r.status_code, r.location)
    r = client.post("/generator/random/step4", data=step4 or STEP4)
    assert r.status_code == 302 and r.location.endswith("/step5"), (r.status_code, r.location)
    r = client.post("/generator/random/step5", data=step5 or STEP5)
    assert r.status_code == 302 and r.location.endswith("/step6"), (r.status_code, r.location)
    r = client.post("/generator/random/step6", data=step6 or STEP6)
    assert r.status_code == 302, (r.status_code, r.location)
    return r


# ── Session recovery ─────────────────────────────────────────────────────


def test_advancing_with_no_session_redirects_to_landing(client):
    """step3..step6 need params to be set; without them they redirect."""
    for step in range(3, 7):
        with client.application.test_client() as c:
            r = c.post(f"/generator/random/step{step}", data={"nav": "next"})
            assert r.status_code == 302
            assert "/generator" in r.location


# ── Happy path + contract ────────────────────────────────────────────────


def test_full_happy_path_produces_valid_params(client):
    _walk_happy_path(client)
    r = client.get("/generator/random/params-json")
    assert r.status_code == 200
    params = json.loads(r.data)
    # Must survive the strict 1e-6 sum check inside Params.__post_init__.
    Params(**params)


# ── Regression: 1.0007 slider sum ─────────────────────────────────────────


def test_parent_child_slider_sum_1p0007_renormalises(client):
    """The slider rounds each segment to 4 decimals, which can leave up to
    0.0007 residue. The route must renormalise to exactly 1.0 before
    constructing Params."""
    client.post("/generator/random/step1", data=STEP1)
    client.post("/generator/random/step2", data=STEP2)
    poisoned = dict(STEP3)
    poisoned.update(
        {
            "dist_optional": "0.2502",
            "dist_mandatory": "0.2502",
            "dist_alternative": "0.2502",
            "dist_or": "0.2501",
        }
    )
    r = client.post("/generator/random/step3", data=poisoned)
    assert r.status_code == 302  # reached step4, Params-level sum is 1.0

    # Walk the rest and check total via params-json
    client.post("/generator/random/step4", data=STEP4)
    client.post("/generator/random/step5", data=STEP5)
    params = json.loads(client.get("/generator/random/params-json").data)
    total = (
        params["DIST_OPTIONAL"]
        + params["DIST_MANDATORY"]
        + params["DIST_ALTERNATIVE"]
        + params["DIST_OR"]
        + params["DIST_GROUP_CARDINALITY"]
    )
    assert abs(total - 1.0) < 1e-6


def test_boolean_ops_residue_renormalises(client):
    _walk_happy_path(
        client,
        step4={**STEP4, "prob_and": "0.3334", "prob_or": "0.3333", "prob_implies": "0.1667", "prob_equiv": "0.1666"},
    )
    params = json.loads(client.get("/generator/random/params-json").data)
    total = params["PROB_AND"] + params["PROB_OR_CT"] + params["PROB_IMPLICATION"] + params["PROB_EQUIVALENCE"]
    assert abs(total - 1.0) < 1e-6


def test_extra_constraint_representativeness_is_int_in_session(client):
    _walk_happy_path(client)
    params = json.loads(client.get("/generator/random/params-json").data)
    assert isinstance(params["EXTRA_CONSTRAINT_REPRESENTATIVENESS"], int)
    assert params["EXTRA_CONSTRAINT_REPRESENTATIVENESS"] >= 1


# ── Regression: back navigation keeps state ───────────────────────────────


def test_back_nav_from_step2_preserves_level_flags(client):
    """The step-2 levels must persist across prev-nav (was a bug that
    reset arithmetic/type on every back press)."""
    client.post("/generator/random/step1", data=STEP1)
    client.post(
        "/generator/random/step2",
        data={
            "arithmetic_level": "on",
            "type_level": "on",
            "aggregate_functions": "on",
        },
    )
    r = client.post("/generator/random/step3", data={**STEP3, "nav": "prev"})
    assert r.status_code == 302
    params = json.loads(client.get("/generator/random/params-json").data)
    assert params["ARITHMETIC_LEVEL"] is True
    assert params["TYPE_LEVEL"] is True
    assert params["AGGREGATE_FUNCTIONS"] is True


def test_back_nav_from_step4_preserves_tree_shape(client):
    client.post("/generator/random/step1", data=STEP1)
    client.post("/generator/random/step2", data=STEP2)
    client.post("/generator/random/step3", data={**STEP3, "num_features_max": "17"})
    r = client.post("/generator/random/step4", data={**STEP4, "nav": "prev"})
    assert r.status_code == 302 and r.location.endswith("/step3")
    r = client.get("/generator/random/step3")
    assert r.status_code == 200
    assert b"17" in r.data


def test_back_nav_from_step6_preserves_output_options(client):
    _walk_happy_path(client, step6={"ensure_satisfiable": "on", "feature_count_suffix": "on", "nav": "prev"})
    params = json.loads(client.get("/generator/random/params-json").data)
    assert params["ENSURE_SATISFIABLE"] is True
    assert params["INCLUDE_FEATURE_COUNT_SUFFIX"] is True
