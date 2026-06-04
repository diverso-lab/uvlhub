from werkzeug.datastructures import MultiDict

from app.modules.generator.wizard_state import (
    clear_step_state,
    load_step_state,
    save_step_state,
)


def test_save_step_state_preserves_checkbox_false_values(test_client):
    with test_client.application.test_request_context():
        from flask import session

        session["wizard"] = {}
        form = MultiDict({"field": "value", "flag": "on"})

        save_step_state(2, form, checkbox_fields=["flag", "missing_flag"])

        assert session["wizard"]["2"]["field"] == "value"
        assert session["wizard"]["2"]["flag"] is True
        assert session["wizard"]["2"]["missing_flag"] is False


def test_load_step_state_merges_saved_values_over_defaults(test_client):
    with test_client.application.test_request_context():
        from flask import session

        session["wizard"] = {"3": {"value": "saved"}}

        values = load_step_state(3, {"value": "default", "other": "x"})

        assert values["value"] == "saved"
        assert values["other"] == "x"


def test_save_step_state_does_not_overwrite_other_steps(test_client):
    with test_client.application.test_request_context():
        from flask import session

        session["wizard"] = {
            "2": {"arithmetic_level": True},
            "4": {"num_constraints_min": "1"},
        }

        save_step_state(3, MultiDict({"num_features_max": "20"}))

        assert session["wizard"]["2"]["arithmetic_level"] is True
        assert session["wizard"]["3"]["num_features_max"] == "20"
        assert session["wizard"]["4"]["num_constraints_min"] == "1"


def test_clear_step_state_only_removes_target_step(test_client):
    with test_client.application.test_request_context():
        from flask import session

        session["wizard"] = {
            "2": {"arithmetic_level": True},
            "3": {"num_features_max": "20"},
        }

        clear_step_state(3)

        assert "3" not in session["wizard"]
        assert session["wizard"]["2"]["arithmetic_level"] is True