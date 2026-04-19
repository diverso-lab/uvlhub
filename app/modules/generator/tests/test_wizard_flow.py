"""End-to-end wizard tests driven through Flask's test client.

The goal is to exercise the happy path and every bug we've already fixed so
none of them can regress silently:

- 1.0007 sum from the parent-child slider
- EXTRA_CONSTRAINT_REPRESENTATIVENESS arriving as 0.5 (vendor default)
- Spanish-locale decimal comma in form fields
- Session corruption → redirect to landing
- Back navigation preserving state
- /generator/random and /generator/llm routes
"""
import json

import pytest

from fm_generator.FMGenerator.models.config import Params


STEP1 = {"num_models_val": "3", "seed": "42", "name_prefix": "fm"}
STEP2 = {
    "num_features_min": "5",
    "num_features_max": "20",
    "max_tree_depth": "5",
    "dist_optional": "0.3",
    "dist_mandatory": "0.3",
    "dist_alternative": "0.2",
    "dist_or": "0.2",
    "nav": "next",
}
STEP3 = {
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
STEP4 = {"random_attributes": "on", "min_attributes": "1", "max_attributes": "3", "nav": "next"}


@pytest.fixture
def client(test_app):
    """Per-test Flask client so sessions don't leak between tests."""
    with test_app.test_client() as c:
        yield c


def _walk_happy_path(client, step2=None, step3=None, step4=None):
    """Walk from step1 through to step4 next and return the final response."""
    r = client.post("/generator/random/step1", data=STEP1)
    assert r.status_code == 302 and r.location.endswith("/step2"), (r.status_code, r.location)
    r = client.post("/generator/random/step2", data=step2 or STEP2)
    assert r.status_code == 302 and r.location.endswith("/step3"), (r.status_code, r.location)
    r = client.post("/generator/random/step3", data=step3 or STEP3)
    assert r.status_code == 302 and r.location.endswith("/step4"), (r.status_code, r.location)
    r = client.post("/generator/random/step4", data=step4 or STEP4)
    assert r.status_code == 302 and r.location.endswith("/step5"), (r.status_code, r.location)
    return r


# ── Routes & top-level shape ─────────────────────────────────────────────

def test_landing_is_reachable(client):
    assert client.get("/generator").status_code == 200
    assert client.get("/generator/").status_code == 200


def test_random_entry_redirects_to_step1(client):
    r = client.get("/generator/random")
    assert r.status_code == 302
    assert r.location.endswith("/step1")


def test_llm_placeholder_renders(client):
    r = client.get("/generator/llm")
    assert r.status_code == 200
    assert b"Coming soon" in r.data


# ── Session recovery ─────────────────────────────────────────────────────

def test_advancing_with_no_session_redirects_to_landing(client):
    """Formerly returned a 400 "Error: Params missing in session" — now we
    redirect the user back to /generator so they can restart cleanly. This
    path triggers on step3 and step4 advance with no session."""
    # Step3 "next" with no session
    r = client.post("/generator/random/step3", data={**STEP3, "nav": "next"})
    assert r.status_code == 302
    assert r.location.endswith("/generator/"), r.location


# ── Happy path + contract ────────────────────────────────────────────────

def test_full_happy_path_produces_valid_params(client):
    _walk_happy_path(client)
    r = client.get("/generator/random/params-json")
    assert r.status_code == 200
    params = json.loads(r.data)
    # Must survive the strict 1e-6 sum check inside Params.__post_init__.
    Params(**params)


def test_step5_renders_when_session_ready(client):
    _walk_happy_path(client)
    r = client.get("/generator/random/step5")
    assert r.status_code == 200


# ── Regression: 1.0007 slider sum ─────────────────────────────────────────

def test_parent_child_slider_sum_1p0007_renormalises(client):
    """The slider rounds each segment to 4 decimals, which can leave up to
    0.0007 residue. The route must renormalise to exactly 1.0 before
    constructing Params."""
    client.post("/generator/random/step1", data=STEP1)
    poisoned = dict(STEP2)
    poisoned.update({
        "dist_optional": "0.2502",
        "dist_mandatory": "0.2502",
        "dist_alternative": "0.2502",
        "dist_or": "0.2501",
    })
    r = client.post("/generator/random/step2", data=poisoned)
    assert r.status_code == 302  # reached step3, Params built OK

    params = json.loads(client.get("/generator/random/params-json").data)
    total = (
        params["DIST_OPTIONAL"] + params["DIST_MANDATORY"]
        + params["DIST_ALTERNATIVE"] + params["DIST_OR"]
        + params["DIST_GROUP_CARDINALITY"]
    )
    assert abs(total - 1.0) < 1e-6


# ── Regression: boolean-ops sum residue ───────────────────────────────────

def test_boolean_ops_residue_renormalises(client):
    _walk_happy_path(
        client,
        step3={**STEP3,
               "prob_and": "0.3334", "prob_or": "0.3333",
               "prob_implies": "0.1667", "prob_equiv": "0.1666"},
    )
    params = json.loads(client.get("/generator/random/params-json").data)
    total = (
        params["PROB_AND"] + params["PROB_OR_CT"]
        + params["PROB_IMPLICATION"] + params["PROB_EQUIVALENCE"]
    )
    assert abs(total - 1.0) < 1e-6


# ── Regression: EXTRA_CONSTRAINT_REPRESENTATIVENESS "0.5" ─────────────────

def test_extra_constraint_representativeness_is_int_in_session(client):
    _walk_happy_path(client)
    params = json.loads(client.get("/generator/random/params-json").data)
    assert isinstance(params["EXTRA_CONSTRAINT_REPRESENTATIVENESS"], int)
    assert params["EXTRA_CONSTRAINT_REPRESENTATIVENESS"] >= 1


# ── Regression: Spanish-locale decimal comma ──────────────────────────────

def test_spanish_locale_decimal_comma_is_accepted(client):
    _walk_happy_path(
        client,
        step3={**STEP3,
               "prob_not": "0,3",
               "prob_and": "0,4", "prob_or": "0,2",
               "prob_implies": "0,2", "prob_equiv": "0,2"},
    )
    params = json.loads(client.get("/generator/random/params-json").data)
    assert params["PROB_NOT"] == pytest.approx(0.3)


# ── Regression: back navigation keeps state ───────────────────────────────

def test_back_nav_from_step3_preserves_step2_choices(client):
    # Advance to step3 with a specific max_features
    client.post("/generator/random/step1", data=STEP1)
    client.post("/generator/random/step2", data={**STEP2, "num_features_max": "17"})

    # Go back from step3 → step2
    r = client.post("/generator/random/step3", data={**STEP3, "nav": "prev"})
    assert r.status_code == 302 and r.location.endswith("/step2")

    # Step2 GET should still show num_features_max=17
    r = client.get("/generator/random/step2")
    assert r.status_code == 200
    assert b"17" in r.data
