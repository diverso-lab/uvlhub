import os
from zipfile import ZipFile

from flask import session
from app.modules.generator.repositories import GeneratorRepository
from core.services.BaseService import BaseService


class GeneratorService(BaseService):
    def __init__(self):
        super().__init__(GeneratorRepository())

    def zip_generated_models(self, output_dir, zip_path):
        """Crea un zip con todos los modelos generados en output_dir."""
        with ZipFile(zip_path, "w") as zipf:
            for root, dirs, files in os.walk(output_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    # El arcname hace que dentro del zip se vea solo el nombre,
                    # no la ruta absoluta
                    arcname = os.path.relpath(file_path, output_dir)
                    zipf.write(file_path, arcname=arcname)


def safe_float(value, default=0.0):
    try:
        fallback = float(default)
    except (TypeError, ValueError):
        fallback = 0.0

    if value is None:
        return fallback

    text = str(value).strip().replace(",", ".")
    if text == "":
        return fallback

    try:
        return float(text)
    except ValueError:
        return fallback


def normalize_distribution(params_dict: dict, keys: list[str], fallback_key: str | None = None) -> None:
    total = sum(float(params_dict.get(k, 0.0)) for k in keys)

    if total > 0:
        for k in keys:
            params_dict[k] = round(float(params_dict.get(k, 0.0)) / total, 6)

        residue = round(1.0 - sum(params_dict[k] for k in keys), 6)
        target = fallback_key or keys[-1]
        params_dict[target] = round(params_dict[target] + residue, 6)
    elif fallback_key:
        for k in keys:
            params_dict[k] = 0.0
        params_dict[fallback_key] = 1.0

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


# ─── Attribute helpers (manual mode) — unchanged semantics ───────────────


def collect_manual_attributes(form, params_dict):
    attr_count = 0
    while f"attr_name_{attr_count}" in form:
        attr_count += 1

    attributes_data, attach_probs, in_constraints = [], [], []

    for i in range(attr_count):
        name = form.get(f"attr_name_{i}", "")
        type_ = form.get(f"attr_type_{i}", "").strip().lower()
        attach_prob = safe_float(form.get(f"attr_attach_prob_{i}"), 1.0)
        raw_use = form.get(f"attr_use_in_constraints_{i}") == "on"

        if type_ == "boolean":
            use_in_ctc = raw_use
        elif type_ in ("integer", "real"):
            use_in_ctc = raw_use and params_dict.get("ARITHMETIC_LEVEL", False)
        elif type_ == "string":
            use_in_ctc = (
                raw_use
                and params_dict.get("TYPE_LEVEL", False)
                and params_dict.get("STRING_CONSTRAINTS", False)
            )
        else:
            use_in_ctc = False

        if type_ == "boolean":
            values_list = []
            if form.get(f"attr_value_true_{i}") is not None:
                values_list.append(True)
            if form.get(f"attr_value_false_{i}") is not None:
                values_list.append(False)

            attr_dict = {
                "name": name,
                "type": "Boolean",
                "value": values_list,
                "attach_probability": attach_prob,
                "use_in_constraints": use_in_ctc,
            }

        elif type_ in ("integer", "real", "string"):
            attr_dict = {
                "name": name,
                "type": type_.capitalize(),
                "min_value": form.get(f"attr_min_value_{i}", None),
                "max_value": form.get(f"attr_max_value_{i}", None),
                "attach_probability": attach_prob,
                "use_in_constraints": use_in_ctc,
            }
        else:
            continue

        attributes_data.append(attr_dict)
        attach_probs.append(attach_prob)
        in_constraints.append(use_in_ctc)

    return attributes_data, attach_probs, in_constraints