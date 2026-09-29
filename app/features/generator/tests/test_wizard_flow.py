"""End-to-end wizard tests driven through Flask's test client.

The wizard is 6 steps:
    1 Batch → 2 Levels → 3 Tree → 4 Constraints → 5 Attributes → 6 Output.

Each step has its own URL (``/generator/random/stepN``) and only persists
the fields it owns. These tests exercise the happy path and the regression
scenarios we've already fixed.
"""

import json

import pytest
from flamapy.metamodels.fm_generator.models import FmgeneratorModel
from flask import Response

from app.features.generator import routes, wizard

pytestmark = pytest.mark.integration

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
    "dist_boolean_atr": "1.0",
    "dist_integer_atr": "0.0",
    "dist_real_atr": "0.0",
    "dist_string_atr": "0.0",
    "nav": "next",
}
STEP6 = {"nav": "next"}


@pytest.fixture
def client(test_app):
    with test_app.test_client() as c:
        yield c


def _set_params(client, **extra):
    params = {
        "NUM_MODELS": 1,
        "SEED": 42,
        "NAME_PREFIX": "fm",
        "MAX_FEATURES": 20,
        "ARITHMETIC_LEVEL": False,
        "TYPE_LEVEL": False,
        "FEATURE_CARDINALITY": False,
        "AGGREGATE_FUNCTIONS": False,
        "STRING_CONSTRAINTS": False,
        "GROUP_CARDINALITY": False,
    }
    params.update(extra)
    with client.session_transaction() as session:
        session["params"] = params


def _valid_step3_data(**extra):
    data = {
        "num_features_min": "5",
        "num_features_max": "20",
        "max_tree_depth": "5",
        "dist_optional": "0.3",
        "dist_mandatory": "0.3",
        "dist_alternative": "0.2",
        "dist_or": "0.2",
        "nav": "next",
    }
    data.update(extra)
    return data


def _valid_step4_data(**extra):
    data = {
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
    data.update(extra)
    return data


def test_landing_resets_both_session_sections(client):
    with client.session_transaction() as session:
        session["params"] = {"SEED": 1}
        session["wizard"] = {"2": {"type_level": True}}

    response = client.get("/generator")

    assert response.status_code == 200
    with client.session_transaction() as session:
        assert "params" not in session
        assert "wizard" not in session


@pytest.mark.parametrize("path", ["/generator/random", "/generator/random/"])
def test_random_entry_redirects_to_step1(client, path):
    response = client.get(path)

    assert response.status_code == 302
    assert response.location.endswith("/generator/random/step1")


@pytest.mark.parametrize("path", ["/generator/llm", "/generator/llm/"])
def test_llm_page_is_reachable(client, path):
    response = client.get(path)

    assert response.status_code == 200


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


# -- Browser assets -------------------------------------------------------


def test_js_asset_sets_runtime_mimetype_for_mjs(client, monkeypatch):
    calls = []

    def fake_send_from_directory(directory, filename):
        calls.append((directory, filename))
        return Response("asset")

    monkeypatch.setattr(routes, "send_from_directory", fake_send_from_directory)

    response = client.get("/generator/js/pyodide/pyodide.mjs")

    assert response.status_code == 200
    assert response.headers["Content-Type"] == "text/javascript"
    assert calls and calls[0][1] == "pyodide/pyodide.mjs"


def test_js_asset_keeps_default_mimetype_for_unknown_extension(client, monkeypatch):
    def fake_send_from_directory(directory, filename):
        return Response("asset")

    monkeypatch.setattr(routes, "send_from_directory", fake_send_from_directory)

    response = client.get("/generator/js/readme.txt")

    assert response.status_code == 200
    assert response.headers["Content-Type"] != "text/javascript"


# ── Session recovery ─────────────────────────────────────────────────────


def test_step1_get_renders_saved_values(client):
    with client.session_transaction() as session:
        session["params"] = {"NUM_MODELS": 7, "SEED": 99, "NAME_PREFIX": "saved"}

    response = client.get("/generator/random/step1")

    assert response.status_code == 200
    assert b"saved" in response.data


def test_step1_invalid_post_renders_errors(client):
    response = client.post(
        "/generator/random/step1",
        data={"num_models_val": "0", "seed": "0", "name_prefix": "fm"},
    )

    assert response.status_code == 200


def test_step2_get_and_invalid_post_render_the_form(client):
    assert client.get("/generator/random/step2").status_code == 200

    # A minor level without its major level is invalid.
    response = client.post(
        "/generator/random/step2",
        data={"feature_cardinality": "on", "nav": "next"},
    )

    assert response.status_code == 200


def test_step2_previous_navigation_redirects_to_step1(client):
    response = client.post(
        "/generator/random/step2",
        data={"arithmetic_level": "on", "nav": "prev"},
    )

    assert response.status_code == 302
    assert response.location.endswith("/generator/random/step1")


def test_advancing_with_no_session_redirects_to_landing(client):
    """step3..step6 need params to be set; without them they redirect."""
    for step in range(3, 7):
        with client.application.test_client() as c:
            r = c.post(f"/generator/random/step{step}", data={"nav": "next"})
            assert r.status_code == 302
            assert "/generator" in r.location


@pytest.mark.parametrize("step", [3, 4, 5, 6])
def test_steps_three_to_six_without_params_redirect_to_landing(client, step):
    response = client.get(f"/generator/random/step{step}")

    assert response.status_code == 302
    assert response.location.rstrip("/").endswith("/generator")


def test_step3_get_and_invalid_post_render_the_form(client):
    _set_params(client)
    assert client.get("/generator/random/step3").status_code == 200

    response = client.post(
        "/generator/random/step3",
        data=_valid_step3_data(num_features_min="20", num_features_max="5"),
    )

    assert response.status_code == 200


def test_step4_get_handles_invalid_saved_ecr_and_saved_field_values(client):
    _set_params(client, EXTRA_CONSTRAINT_REPRESENTATIVENESS="invalid")
    with client.session_transaction() as session:
        session["wizard"] = {"4": {"vars_per_ctc_max": "invalid"}}

    response = client.get("/generator/random/step4")

    assert response.status_code == 200


def test_step4_invalid_post_renders_the_form(client):
    _set_params(client)

    response = client.post(
        "/generator/random/step4",
        data=_valid_step4_data(num_constraints_min="10", num_constraints_max="1"),
    )

    assert response.status_code == 200


def test_step5_get_and_invalid_post_render_the_form(client):
    _set_params(client)
    assert client.get("/generator/random/step5").status_code == 200

    response = client.post(
        "/generator/random/step5",
        data={
            "random_attributes": "on",
            "min_attributes": "5",
            "max_attributes": "1",
            "dist_boolean_atr": "1",
            "dist_integer_atr": "0",
            "dist_real_atr": "0",
            "dist_string_atr": "0",
            "nav": "next",
        },
    )

    assert response.status_code == 200


def test_step6_get_and_previous_navigation(client):
    _set_params(client)
    assert client.get("/generator/random/step6").status_code == 200

    response = client.post(
        "/generator/random/step6",
        data={"ensure_satisfiable": "on", "nav": "prev"},
    )

    assert response.status_code == 302
    assert response.location.endswith("/generator/random/step5")


# ── Happy path + contract ────────────────────────────────────────────────


def test_full_happy_path_produces_valid_params(client):
    _walk_happy_path(client)
    r = client.get("/generator/random/params-json")
    assert r.status_code == 200
    params = json.loads(r.data)
    # Must survive the strict 1e-6 sum check inside FmgeneratorModel validation.
    FmgeneratorModel.from_flat_dict(params)


def test_params_json_returns_400_without_params(client):
    response = client.get("/generator/random/params-json")

    assert response.status_code == 400
    assert response.get_json() == {"error": "Params missing"}


# ── Regression: 1.0007 slider sum ─────────────────────────────────────────


def test_parent_child_slider_sum_1p0007_renormalises(client):
    """The slider rounds each segment to 4 decimals, which can leave up to
    0.0007 residue. The route must renormalise to exactly 1.0 before
    constructing FmgeneratorModel."""
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
    assert r.status_code == 302  # reached step4, generator-model-level sum is 1.0

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


def test_step4_configuration_survives_forward_and_back_navigation(client):
    """Step 4 constraint configuration must survive leaving the step and
    coming back later. Users should only lose values when they explicitly
    modify them, not because of wizard navigation."""
    client.post("/generator/random/step1", data=STEP1)
    client.post(
        "/generator/random/step2",
        data={
            "arithmetic_level": "on",
            "type_level": "on",
            "aggregate_functions": "on",
            "string_constraints": "on",
        },
    )
    client.post("/generator/random/step3", data=STEP3)

    custom_step4 = {
        **STEP4,
        "prob_plus": "0.55",
        "prob_minus": "0.15",
        "prob_times": "0.10",
        "prob_div": "0.05",
        "prob_sum": "0.10",
        "prob_avg": "0.05",
        "prob_eq": "0.25",
        "prob_lt": "0.25",
        "prob_gt": "0.25",
        "prob_leq": "0.15",
        "prob_geq": "0.10",
        "prob_len": "0.90",
        "ctc_dist_boolean": "0.7",
        "ctc_dist_integer": "0.2",
        "ctc_dist_real": "0.1",
        "ctc_dist_string": "0.0",
    }

    # Step 4 -> Step 5
    r = client.post("/generator/random/step4", data=custom_step4)
    assert r.status_code == 302
    assert r.location.endswith("/step5")

    # Step 5 -> Step 4
    r = client.post("/generator/random/step5", data={**STEP5, "nav": "prev"})
    assert r.status_code == 302
    assert r.location.endswith("/step4")

    # The form should be restored with the previous values
    r = client.get("/generator/random/step4")
    assert r.status_code == 200

    assert b'value="0.55"' in r.data  # prob_plus
    assert b'value="0.15"' in r.data  # prob_minus
    assert b'value="0.90"' in r.data  # prob_len


def test_back_nav_from_step6_preserves_output_options(client):
    _walk_happy_path(client, step6={"ensure_satisfiable": "on", "feature_count_suffix": "on", "nav": "prev"})
    params = json.loads(client.get("/generator/random/params-json").data)
    assert params["ENSURE_SATISFIABLE"] is True
    assert params["INCLUDE_FEATURE_COUNT_SUFFIX"] is True


# -- SAT endpoint ---------------------------------------------------------


def test_generate_sat_returns_models(client, monkeypatch):
    monkeypatch.setattr(
        wizard.GeneratorWizardService,
        "generate_sat_models",
        staticmethod(lambda data: [{"filename": "fm.uvl"}]),
    )

    response = client.post("/generator/random/generate-sat", json={"SEED": 42})

    assert response.status_code == 200
    assert response.get_json() == {"models": [{"filename": "fm.uvl"}]}


def test_generate_sat_returns_400_without_json(client):
    response = client.post("/generator/random/generate-sat", json={})

    assert response.status_code == 400
    assert response.get_json() == {
        "error": "Missing generation parameters.",
        "code": "MISSING_PARAMETERS",
    }


def test_generate_sat_returns_500_when_generation_fails(client, monkeypatch):
    def fail(data):
        raise RuntimeError("generation failed")

    monkeypatch.setattr(
        wizard.GeneratorWizardService,
        "generate_sat_models",
        staticmethod(fail),
    )

    response = client.post(
        "/generator/random/generate-sat",
        json={"SEED": 42},
    )

    assert response.status_code == 500
    assert response.get_json() == {
        "error": "SAT-checked generation could not be completed.",
        "code": "SAT_GENERATION_ERROR",
    }


# -- Live summary endpoint -------------------------------------------------


def test_summary_refresh_step1_clamps_values_and_handles_invalid_input(client):
    response = client.post(
        "/generator/random/summary-refresh/1",
        data={"num_models_val": "5000", "seed": "0", "name_prefix": "draft"},
    )
    assert response.status_code == 200

    with client.session_transaction() as session:
        assert session["params"]["NUM_MODELS"] == 1000
        assert session["params"]["SEED"] == 1
        assert session["params"]["NAME_PREFIX"] == "draft"

    response = client.post(
        "/generator/random/summary-refresh/1",
        data={"num_models_val": "bad", "seed": "bad"},
    )
    assert response.status_code == 200


def test_summary_refresh_swallows_persister_errors(client, monkeypatch):
    _set_params(client)

    def fail(params, form):
        raise ValueError("incomplete draft")

    monkeypatch.setitem(routes._DRAFT_PERSISTERS, 2, fail)

    response = client.post(
        "/generator/random/summary-refresh/2",
        data={"arithmetic_level": "on"},
    )

    assert response.status_code == 200
    with client.session_transaction() as session:
        assert session["params"]["NUM_MODELS"] == 1
