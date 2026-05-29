from flask import session

from app.modules.generator.wizard_persisters import (
    apply_step2_levels,
    apply_step3_tree,
    apply_step4_constraints,
    apply_step5_attributes,
    apply_step6_output,
)


def save_step_state(step: int, form, checkbox_fields=None):
    checkbox_fields = checkbox_fields or []
    wizard = session.get("wizard", {})
    data = dict(form)

    for cb in checkbox_fields:
        data[cb] = cb in form

    wizard[str(step)] = data
    session["wizard"] = wizard


def clear_step_state(step: int):
    wizard = session.get("wizard", {})

    if wizard.pop(str(step), None) is not None:
        session["wizard"] = wizard


def load_step_state(step: int, defaults: dict):
    wizard = session.get("wizard", {})
    saved = wizard.get(str(step), {})

    out = defaults.copy()
    out.update(saved)

    return out


DRAFT_PERSISTERS = {
    2: apply_step2_levels,
    3: apply_step3_tree,
    4: apply_step4_constraints,
    5: apply_step5_attributes,
    6: apply_step6_output,
}


def update_summary_draft(step: int, form) -> dict:
    params_dict = session.get("params", {}) or {}

    if step == 1:
        try:
            nm = form.get("num_models_val")
            if nm:
                params_dict["NUM_MODELS"] = max(1, min(1000, int(nm)))
        except (TypeError, ValueError):
            pass

        try:
            sd = form.get("seed")
            if sd:
                params_dict["SEED"] = max(1, int(sd))
        except (TypeError, ValueError):
            pass

        if form.get("name_prefix") is not None:
            params_dict["NAME_PREFIX"] = form.get("name_prefix", "")

    elif step in DRAFT_PERSISTERS:
        try:
            DRAFT_PERSISTERS[step](params_dict, form)
        except Exception:
            pass

    session["params"] = params_dict
    return params_dict
