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


# ─── Step form persistence helpers ───────────────────────────────────────


def apply_step2_levels(params_dict, form):
    """Persist only the level toggles from step 2.

    Normalises the hierarchy so session state matches what
    ``Params.__post_init__`` would produce:
      * TYPE_LEVEL → ARITHMETIC_LEVEL (typed attrs imply arithmetic).
      * Minor levels (feature/aggregate, string) are cleared when their
        major is off.
    """
    # Boolean is the base level — always on once step 2 has been visited,
    # so the summary sidebar always lists "Majors: Boolean, …" from here on.
    params_dict["BOOLEAN_LEVEL"] = True
    params_dict["ARITHMETIC_LEVEL"] = "arithmetic_level" in form
    params_dict["TYPE_LEVEL"] = "type_level" in form
    params_dict["FEATURE_CARDINALITY"] = "feature_cardinality" in form
    params_dict["AGGREGATE_FUNCTIONS"] = "aggregate_functions" in form
    params_dict["STRING_CONSTRAINTS"] = "string_constraints" in form
    params_dict["GROUP_CARDINALITY"] = "group_cardinality" in form
    if params_dict["TYPE_LEVEL"]:
        params_dict["ARITHMETIC_LEVEL"] = True
    if not params_dict["ARITHMETIC_LEVEL"]:
        params_dict["FEATURE_CARDINALITY"] = False
        params_dict["AGGREGATE_FUNCTIONS"] = False
    if not params_dict["TYPE_LEVEL"]:
        params_dict["STRING_CONSTRAINTS"] = False


def apply_step3_tree(params_dict, form):
    """Persist feature tree + feat/group-cardinality settings from step 3."""
    params_dict["MIN_FEATURES"] = int(form.get("num_features_min", 1))
    params_dict["MAX_FEATURES"] = int(form.get("num_features_max", 10))
    params_dict["MAX_TREE_DEPTH"] = int(form.get("max_tree_depth", 5))

    params_dict["DIST_OPTIONAL"] = safe_float(form.get("dist_optional"), 0.3)
    params_dict["DIST_MANDATORY"] = safe_float(form.get("dist_mandatory"), 0.3)
    params_dict["DIST_ALTERNATIVE"] = safe_float(form.get("dist_alternative"), 0.2)
    params_dict["DIST_OR"] = safe_float(form.get("dist_or"), 0.2)

    if params_dict.get("GROUP_CARDINALITY"):
        params_dict["DIST_GROUP_CARDINALITY"] = safe_float(form.get("dist_group_cardinality"), 0.0)
        params_dict["GROUP_CARDINALITY_MIN"] = int(form.get("group_cardinality_min", 1))
        params_dict["GROUP_CARDINALITY_MAX"] = int(form.get("group_cardinality_max", 6))
    else:
        params_dict["DIST_GROUP_CARDINALITY"] = 0.0

    if params_dict.get("FEATURE_CARDINALITY"):
        params_dict["PROB_FEATURE_CARDINALITY"] = safe_float(form.get("prob_fc"), 0.1)
        params_dict["MIN_FEATURE_CARDINALITY"] = int(form.get("min_feature_cardinality", 2))
        params_dict["MAX_FEATURE_CARDINALITY"] = int(form.get("max_feature_cardinality", 5))
    else:
        params_dict["PROB_FEATURE_CARDINALITY"] = 0.0
        params_dict.pop("MIN_FEATURE_CARDINALITY", None)
        params_dict.pop("MAX_FEATURE_CARDINALITY", None)

    # Renormalise relation distribution so it totals EXACTLY 1.0
    _keys = ["DIST_OPTIONAL", "DIST_MANDATORY", "DIST_ALTERNATIVE", "DIST_OR", "DIST_GROUP_CARDINALITY"]
    normalize_distribution(params_dict, _keys, fallback_key="DIST_OPTIONAL")

def apply_step4_constraints(params_dict, form):
    """Persist constraint counts + all probability distributions from step 4."""
    params_dict["MIN_CONSTRAINTS"] = int(form.get("num_constraints_min", 1))
    params_dict["MAX_CONSTRAINTS"] = int(form.get("num_constraints_max", 10))
    try:
        params_dict["EXTRA_CONSTRAINT_REPRESENTATIVENESS"] = max(1, int(float(form.get("extra_constraint_repr", 1))))
    except (TypeError, ValueError):
        params_dict["EXTRA_CONSTRAINT_REPRESENTATIVENESS"] = 1
    params_dict["MIN_VARS_PER_CONSTRAINT"] = int(form.get("vars_per_ctc_min", 1))
    max_feats = int(params_dict.get("MAX_FEATURES", 10000))
    params_dict["MAX_VARS_PER_CONSTRAINT"] = min(int(form.get("vars_per_ctc_max", 1)), max_feats)

    # Boolean level
    params_dict["PROB_NOT"] = safe_float(form.get("prob_not"), 0.3)
    params_dict["PROB_AND"] = safe_float(form.get("prob_and"), 0.7)
    params_dict["PROB_OR_CT"] = safe_float(form.get("prob_or"), 0.1)
    params_dict["PROB_IMPLICATION"] = safe_float(form.get("prob_implies"), 0.1)
    params_dict["PROB_EQUIVALENCE"] = safe_float(form.get("prob_equiv"), 0.1)
    # Renormalise boolean connectives to exact 1.0
    bkeys = ["PROB_AND", "PROB_OR_CT", "PROB_IMPLICATION", "PROB_EQUIVALENCE"]
    normalize_distribution(params_dict, bkeys, fallback_key="PROB_AND")

    arith_on = bool(params_dict.get("ARITHMETIC_LEVEL", False))
    agg_on = bool(params_dict.get("AGGREGATE_FUNCTIONS", False))
    if arith_on:
        params_dict["PROB_SUM"] = safe_float(form.get("prob_plus"), 0.7)
        params_dict["PROB_SUBSTRACT"] = safe_float(form.get("prob_minus"), 0.2)
        params_dict["PROB_MULTIPLY"] = safe_float(form.get("prob_times"), 0.1)
        params_dict["PROB_DIVIDE"] = safe_float(form.get("prob_div"), 0.0)
        if agg_on:
            params_dict["PROB_SUM_FUNCTION"] = safe_float(form.get("prob_sum"), 0.0)
            params_dict["PROB_AVG_FUNCTION"] = safe_float(form.get("prob_avg"), 0.0)
        else:
            params_dict["PROB_SUM_FUNCTION"] = 0.0
            params_dict["PROB_AVG_FUNCTION"] = 0.0
        params_dict["PROB_EQUALS"] = safe_float(form.get("prob_eq"), 0.1)
        params_dict["PROB_LESS"] = safe_float(form.get("prob_lt"), 0.2)
        params_dict["PROB_GREATER"] = safe_float(form.get("prob_gt"), 0.7)
        params_dict["PROB_LESS_EQUALS"] = safe_float(form.get("prob_leq"), 0.0)
        params_dict["PROB_GREATER_EQUALS"] = safe_float(form.get("prob_geq"), 0.0)
    else:
        for k in (
            "PROB_SUM",
            "PROB_SUBSTRACT",
            "PROB_MULTIPLY",
            "PROB_DIVIDE",
            "PROB_SUM_FUNCTION",
            "PROB_AVG_FUNCTION",
            "PROB_EQUALS",
            "PROB_LESS",
            "PROB_GREATER",
            "PROB_LESS_EQUALS",
            "PROB_GREATER_EQUALS",
        ):
            params_dict[k] = 0.0

    type_on = bool(params_dict.get("TYPE_LEVEL", False))
    str_on = bool(params_dict.get("STRING_CONSTRAINTS", False))
    if type_on and str_on:
        params_dict["PROB_LEN_FUNCTION"] = safe_float(form.get("prob_len"), 0.7)
    else:
        params_dict["PROB_LEN_FUNCTION"] = 0.0

    # CTC type distribution
    params_dict["CTC_DIST_BOOLEAN"] = safe_float(
        form.get("ctc_dist_boolean"),
        0.7 if arith_on or type_on else 1.0,
    )
    params_dict["CTC_DIST_INTEGER"] = (
        safe_float(form.get("ctc_dist_integer"), 0.2)
        if arith_on else 0.0
    )
    params_dict["CTC_DIST_REAL"] = (
        safe_float(form.get("ctc_dist_real"), 0.1)
        if arith_on else 0.0
    )
    params_dict["CTC_DIST_STRING"] = (
        safe_float(form.get("ctc_dist_string"), 0.0)
        if type_on and str_on else 0.0
    )

    # Remove obsolete keys from older sessions / previous implementation.
    params_dict.pop("CTC_DIST_NUMERIC", None)
    params_dict.pop("CTC_DIST_AGGREGATE", None)

    cks = [
        "CTC_DIST_BOOLEAN",
        "CTC_DIST_INTEGER",
        "CTC_DIST_REAL",
        "CTC_DIST_STRING",
    ]
    
    normalize_distribution(params_dict, cks, fallback_key="CTC_DIST_BOOLEAN")


def apply_step5_attributes(params_dict, form):
    """Persist attribute settings from step 5."""
    random_attributes = "random_attributes" in form
    params_dict["RANDOM_ATTRIBUTES"] = random_attributes
    if random_attributes:
        params_dict["MIN_ATTRIBUTES"] = int(form.get("min_attributes", 1))
        params_dict["MAX_ATTRIBUTES"] = int(form.get("max_attributes", 5))
        params_dict["ATTRIBUTES_LIST"] = []
        params_dict["ATTRIBUTE_ATTACH_PROBS"] = []
        params_dict["ATTRIBUTE_IN_CONSTRAINTS"] = []
        arith_on = bool(params_dict.get("ARITHMETIC_LEVEL", False))
        type_on = bool(params_dict.get("TYPE_LEVEL", False))
        dist = {
            "DIST_BOOLEAN": safe_float(form.get("dist_boolean"), 0.7),
            "DIST_INTEGER": safe_float(form.get("dist_integer"), 0.0) if arith_on else 0.0,
            "DIST_REAL": safe_float(form.get("dist_real"), 0.0) if arith_on else 0.0,
            "DIST_STRING": safe_float(form.get("dist_string"), 0.0) if type_on else 0.0,
        }
        params_dict.update(dist)
        normalize_distribution(
            params_dict,
            ["DIST_BOOLEAN", "DIST_INTEGER", "DIST_REAL", "DIST_STRING"],
            fallback_key="DIST_BOOLEAN",
        )
    else:
        attrs, probs, in_ctc = collect_manual_attributes(form, params_dict)
        params_dict["MIN_ATTRIBUTES"] = None
        params_dict["MAX_ATTRIBUTES"] = None
        params_dict["ATTRIBUTES_LIST"] = attrs
        params_dict["ATTRIBUTE_ATTACH_PROBS"] = probs
        params_dict["ATTRIBUTE_IN_CONSTRAINTS"] = in_ctc


def apply_step6_output(params_dict, form):
    """Persist output options from step 6."""
    params_dict["ENSURE_SATISFIABLE"] = "ensure_satisfiable" in form
    params_dict["INCLUDE_FEATURE_COUNT_SUFFIX"] = "feature_count_suffix" in form
    params_dict["INCLUDE_CONSTRAINT_COUNT_SUFFIX"] = "constraint_count_suffix" in form
