from werkzeug.datastructures import MultiDict

from app.modules.generator.wizard_state import (
    load_step_state,
    save_step_state,
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