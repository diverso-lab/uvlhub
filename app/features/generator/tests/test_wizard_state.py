import pytest
from flask import session
from werkzeug.datastructures import MultiDict

from app.features.generator.wizard import (
    load_step_state,
    save_step_state,
)

pytestmark = pytest.mark.integration


def test_save_step_state_preserves_checkbox_false_values(test_client):
    with test_client.application.test_request_context():
        session["wizard"] = {}
        form = MultiDict({"field": "value", "flag": "on"})

        save_step_state(2, form, checkbox_fields=["flag", "missing_flag"])

        assert session["wizard"]["2"]["field"] == "value"
        assert session["wizard"]["2"]["flag"] is True
        assert session["wizard"]["2"]["missing_flag"] is False


def test_load_step_state_merges_saved_values_over_defaults(test_client):
    with test_client.application.test_request_context():
        session["wizard"] = {"3": {"value": "saved"}}

        values = load_step_state(3, {"value": "default", "other": "x"})

        assert values["value"] == "saved"
        assert values["other"] == "x"


def test_save_step_state_does_not_overwrite_other_steps(test_client):
    with test_client.application.test_request_context():
        session["wizard"] = {
            "2": {"arithmetic_level": True},
            "4": {"num_constraints_min": "1"},
        }

        save_step_state(3, MultiDict({"num_features_max": "20"}))

        assert session["wizard"]["2"]["arithmetic_level"] is True
        assert session["wizard"]["3"]["num_features_max"] == "20"
        assert session["wizard"]["4"]["num_constraints_min"] == "1"


def test_step_state_is_preserved_after_returning_to_previous_step(test_client):
    with test_client.application.test_request_context():
        session["wizard"] = {}

        form = MultiDict(
            {
                "prob_plus": "0.5",
                "prob_minus": "0.3",
                "prob_times": "0.2",
                "prob_div": "0.0",
                "prob_len": "0.9",
            }
        )

        save_step_state(4, form)

        values = load_step_state(
            4,
            {
                "prob_plus": "0.7",
                "prob_minus": "0.2",
                "prob_times": "0.1",
                "prob_div": "0.0",
                "prob_len": "0.7",
            },
        )

        assert values["prob_plus"] == "0.5"
        assert values["prob_minus"] == "0.3"
        assert values["prob_times"] == "0.2"
        assert values["prob_len"] == "0.9"
