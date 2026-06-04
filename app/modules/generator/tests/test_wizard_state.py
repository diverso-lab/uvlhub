from werkzeug.datastructures import MultiDict

from app.modules.generator.wizard_state import (
    clear_step_state,
    load_step_state,
    save_step_state,
<<<<<<< HEAD
)


def test_save_step_state_preserves_checkbox_false_values(test_client):
=======
    update_summary_draft,
)


def test_save_step_state_with_checkbox(test_client):
>>>>>>> 352a7cc12088baf77fcee5bfaaa24d6953cf95d3
    with test_client.application.test_request_context():
        from flask import session

        session["wizard"] = {}
        form = MultiDict({"field": "value", "flag": "on"})

        save_step_state(2, form, checkbox_fields=["flag", "missing_flag"])

        assert session["wizard"]["2"]["field"] == "value"
        assert session["wizard"]["2"]["flag"] is True
        assert session["wizard"]["2"]["missing_flag"] is False


<<<<<<< HEAD
def test_load_step_state_merges_saved_values_over_defaults(test_client):
=======
def test_load_step_state_overrides_defaults(test_client):
>>>>>>> 352a7cc12088baf77fcee5bfaaa24d6953cf95d3
    with test_client.application.test_request_context():
        from flask import session

        session["wizard"] = {"3": {"value": "saved"}}

        values = load_step_state(3, {"value": "default", "other": "x"})

        assert values["value"] == "saved"
        assert values["other"] == "x"


<<<<<<< HEAD
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
=======
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
>>>>>>> 352a7cc12088baf77fcee5bfaaa24d6953cf95d3
