from werkzeug.datastructures import MultiDict

from app.modules.generator.wizard_state import (
    clear_step_state,
    load_step_state,
    save_step_state,
    update_summary_draft,
)


def test_save_step_state_with_checkbox(test_client):
    with test_client.application.test_request_context():
        from flask import session

        session["wizard"] = {}
        form = MultiDict({"field": "value", "flag": "on"})

        save_step_state(2, form, checkbox_fields=["flag", "missing_flag"])

        assert session["wizard"]["2"]["field"] == "value"
        assert session["wizard"]["2"]["flag"] is True
        assert session["wizard"]["2"]["missing_flag"] is False


def test_load_step_state_overrides_defaults(test_client):
    with test_client.application.test_request_context():
        from flask import session

        session["wizard"] = {"3": {"value": "saved"}}

        values = load_step_state(3, {"value": "default", "other": "x"})

        assert values["value"] == "saved"
        assert values["other"] == "x"


def test_clear_step_state(test_client):
    with test_client.application.test_request_context():
        from flask import session

        session["wizard"] = {"2": {"field": "value"}}

        clear_step_state(2)

        assert "2" not in session["wizard"]


def test_update_summary_draft_step1(test_client):
    with test_client.application.test_request_context():
        from flask import session

        session["params"] = {}
        form = MultiDict(
            {
                "num_models_val": "8",
                "seed": "99",
                "name_prefix": "abc",
            }
        )

        params = update_summary_draft(1, form)

        assert params["NUM_MODELS"] == 8
        assert params["SEED"] == 99
        assert params["NAME_PREFIX"] == "abc"
