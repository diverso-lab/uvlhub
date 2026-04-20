from flask import jsonify, redirect, render_template, request, session, url_for

from app.modules.generator import generator_bp
from app.modules.generator.services import GeneratorService

generator_service = GeneratorService()

STEP3_UI_DEFAULTS = {
    # Arithmetic (sin aggregates)
    "prob_plus": 0.7,
    "prob_minus": 0.2,
    "prob_times": 0.1,
    "prob_div": 0.0,
    "prob_sum": 0.0,
    "prob_avg": 0.0,
    # Comparison
    "prob_eq": 0.1,
    "prob_lt": 0.2,
    "prob_gt": 0.7,
    "prob_leq": 0.0,
    "prob_geq": 0.0,
    # (si quieres también len por defecto)
    "prob_len": 0.7,
}


def _safe_float(value, default=0.0):
    """Parse a form value as float, tolerating the Spanish-locale decimal
    comma some browsers submit for ``<input type="number">``. The default
    is always coerced to float so callers can't accidentally propagate a
    string through arithmetic."""
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


def save_step_state(step: int, form, checkbox_fields=None):
    """Cache the raw form values so we can repaint the page if validation fails."""
    checkbox_fields = checkbox_fields or []
    wizard = session.get("wizard", {})

    data = dict(form)  # MultiDict -> dict (solo 1 valor por key)

    # Normaliza checkboxes: si no vienen, es False
    for cb in checkbox_fields:
        data[cb] = cb in form

    wizard[str(step)] = data
    session["wizard"] = wizard


def clear_step_state(step: int):
    """Drop the cached form values for a step once it has advanced cleanly.

    The wizard cache is only useful between POST-with-errors and the re-render
    that follows; after a successful transition the canonical values live in
    session["params"] and the cache would just shadow them on navigation."""
    wizard = session.get("wizard", {})
    if wizard.pop(str(step), None) is not None:
        session["wizard"] = wizard


def load_step_state(step: int, defaults: dict):
    """Carga valores guardados del step (si existen) mezclados con defaults."""
    wizard = session.get("wizard", {})
    saved = wizard.get(str(step), {})
    out = defaults.copy()
    out.update(saved)
    return out


def validate_step1_form(form):
    """Valida los campos del formulario de step1 y devuelve (errores, valores)."""
    errors = {}
    values = {}  # Para rellenar el formulario en caso de error

    num_models_val = form.get("num_models_val", "").strip()
    seed_val = form.get("seed", "").strip()

    # Validar NUM_MODELS
    try:
        num_models = int(num_models_val)
        if num_models < 1:
            errors["num_models_val"] = "Number of models must be at least 1."
        elif num_models > 1000:
            errors["num_models_val"] = "Number of models cannot exceed 1000."
    except Exception:
        errors["num_models_val"] = "Number of models must be an integer."

    # Validar SEED
    try:
        seed = int(seed_val)
        if seed <= 0:
            errors["seed"] = "Seed must be a positive integer."
    except Exception:
        errors["seed"] = "Seed must be a positive integer."

    # Guardar valores introducidos para recargar el formulario
    for k in form:
        values[k] = form[k]

    return errors, values


@generator_bp.route("/generator", methods=["GET"])
@generator_bp.route("/generator/", methods=["GET"])
def landing():
    """Entry page: pick between random generator and LLM generator (coming soon).

    Hitting the landing always resets the wizard state so a new run starts fresh
    without carrying over checkboxes / values from a previous session.
    """
    session.pop("params", None)
    session.pop("wizard", None)
    return render_template("generator/landing.html")


@generator_bp.route("/generator/random", methods=["GET"])
@generator_bp.route("/generator/random/", methods=["GET"])
def random_entry():
    """Entry point for the random-generator wizard — hop to its first step."""
    return redirect(url_for("generator.step1"))


@generator_bp.route("/generator/llm", methods=["GET"])
@generator_bp.route("/generator/llm/", methods=["GET"])
def llm():
    """Placeholder for the upcoming LLM-driven generator."""
    return render_template("generator/llm.html")


# Paso 1: solo guarda los valores y pasa a step2
@generator_bp.route("/generator/random/step1", methods=["GET", "POST"])
def step1():
    if request.method == "POST":
        errors, values = validate_step1_form(request.form)

        if errors:
            return render_template("generator/step1.html", current_step=1, errors=errors, values=values)

        try:
            from fm_generator.FMGenerator.models.config import Params

            params = Params(
                NUM_MODELS=int(request.form.get("num_models_val")),
                SEED=int(request.form.get("seed")),
                ENSURE_SATISFIABLE="ensure_satisfiable" in request.form,
                NAME_PREFIX=request.form.get("name_prefix", ""),
                INCLUDE_FEATURE_COUNT_SUFFIX="feature_count_suffix" in request.form,
                INCLUDE_CONSTRAINT_COUNT_SUFFIX="constraint_count_suffix" in request.form,
            )
        except ValueError as e:
            errors["global"] = str(e)
            return render_template(
                "generator/step1.html",
                current_step=1,
                errors=errors,
                values=request.form,
            )

        session["params"] = params.__dict__
        clear_step_state(1)
        return redirect(url_for("generator.step2"))

    params_dict = session.get("params", {})

    values = {
        "num_models_val": params_dict.get("NUM_MODELS", 5),
        "seed": params_dict.get("SEED", 42),
        "name_prefix": params_dict.get("NAME_PREFIX", ""),
        "ensure_satisfiable": ("on" if params_dict.get("ENSURE_SATISFIABLE", True) else ""),
        "feature_count_suffix": ("on" if params_dict.get("INCLUDE_FEATURE_COUNT_SUFFIX", False) else ""),
        "constraint_count_suffix": ("on" if params_dict.get("INCLUDE_CONSTRAINT_COUNT_SUFFIX", False) else ""),
    }

    return render_template("generator/step1.html", current_step=1, errors={}, values=values)


def validate_step2_form(form):
    errors = {}
    values = {}

    # Features
    min_features_val = form.get("num_features_min", "").strip()
    max_features_val = form.get("num_features_max", "").strip()

    try:
        min_features = int(min_features_val)
        if min_features < 1:
            errors["num_features_min"] = "Min. features must be at least 1."
    except Exception:
        min_features = None
        errors["num_features_min"] = "Min. features must be an integer."

    try:
        max_features = int(max_features_val)
        if max_features < 1:
            errors["num_features_max"] = "Max. features must be at least 1."
    except Exception:
        max_features = None
        errors["num_features_max"] = "Max. features must be an integer."

    if (
        "num_features_min" not in errors
        and "num_features_max" not in errors
        and min_features is not None
        and max_features is not None
        and min_features > max_features
    ):
        errors["num_features_max"] = "Max. features must be greater than or equal to Min. features."

    # MAX_TREE_DEPTH
    max_tree_depth_val = form.get("max_tree_depth", "").strip()
    try:
        max_tree_depth = int(max_tree_depth_val)
        if "num_features_max" not in errors and not (1 <= max_tree_depth <= max_features):
            errors["max_tree_depth"] = "Maximum tree depth must be between 1 and the maximum number of features."
    except Exception:
        errors["max_tree_depth"] = "Maximum tree depth must be an integer."

    # Attach probability (prob_fc)
    prob_fc_val = form.get("prob_fc")
    if prob_fc_val is not None:
        try:
            ap = float(prob_fc_val.strip())
            if not (0.01 <= ap <= 1.0):
                errors["attach_probability"] = "Attach probability must be between 0.01 and 1."
        except Exception:
            errors["attach_probability"] = "Attach probability must be a decimal between 0.01 and 1."

    # Distribución de relaciones (groups)
    rel_fields = ["dist_optional", "dist_mandatory", "dist_alternative", "dist_or"]
    group_cardinality_enabled = "group_cardinality" in form

    if group_cardinality_enabled:
        rel_fields.append("dist_group_cardinality")

    rel_values = []

    for f in rel_fields:
        val = form.get(f, "").strip()
        try:
            v = float(val)
            if not (0.0 <= v <= 1.0):
                errors[f] = "Value must be between 0 and 1."
            rel_values.append(v)
        except Exception:
            errors[f] = "Value must be a decimal between 0 and 1."
            rel_values.append(0.0)
    rel_total = sum(rel_values)
    if abs(rel_total - 1.0) > 0.001:
        for f in rel_fields:
            if f not in errors:
                errors[f] = "The sum of all relation distributions must be exactly 1.0."
        errors["rel_dist_total"] = f"Current sum: {rel_total:.4f}. The total must be 1.0."
    values["rel_dist_total"] = f"{rel_total:.4f}"

    if group_cardinality_enabled:
        group_card_min_val = form.get("group_cardinality_min", "").strip()
        group_card_max_val = form.get("group_cardinality_max", "").strip()

        try:
            group_card_min = int(group_card_min_val)
            if group_card_min < 1:
                errors["group_cardinality_min"] = "Group cardinality min must be at least 1."
        except Exception:
            group_card_min = None
            errors["group_cardinality_min"] = "Group cardinality min must be an integer."

        try:
            group_card_max = int(group_card_max_val)
            if "num_features_max" not in errors and group_card_max > max_features:
                errors["group_cardinality_max"] = (
                    "Group cardinality max cannot be greater than the maximum number of features."
                )
            elif group_card_max < 1:
                errors["group_cardinality_max"] = "Group cardinality max must be at least 1."
        except Exception:
            group_card_max = None
            errors["group_cardinality_max"] = "Group cardinality max must be an integer."

        if (
            "group_cardinality_min" not in errors
            and "group_cardinality_max" not in errors
            and group_card_min is not None
            and group_card_max is not None
            and group_card_min > group_card_max
        ):
            errors["group_cardinality_max"] = "Group cardinality max must be greater than or equal to min."

    # Guardar valores introducidos
    for k in form:
        values[k] = form[k]

    return errors, values


@generator_bp.route("/generator/random/step2", methods=["GET", "POST"])
def step2():
    if request.method == "POST":
        nav = request.form.get("nav", "next")

        save_step_state(
            2,
            request.form,
            checkbox_fields=[
                "boolean_level",
                "group_cardinality",
                "arithmetic_level",
                "feature_cardinality",
                "aggregate_functions",
                "type_level",
                "string_constraints",
            ],
        )

        if nav == "prev":
            # Guardar también en params (best-effort) para que no se pierda si
            # vuelves y luego avanzas
            params_dict = session.get("params", {}) or {}
            params_dict["GROUP_CARDINALITY"] = "group_cardinality" in request.form
            params_dict["MIN_FEATURES"] = int(request.form.get("num_features_min", params_dict.get("MIN_FEATURES", 10)))
            params_dict["MAX_FEATURES"] = int(request.form.get("num_features_max", params_dict.get("MAX_FEATURES", 50)))
            params_dict["MAX_TREE_DEPTH"] = int(
                request.form.get("max_tree_depth", params_dict.get("MAX_TREE_DEPTH", 5))
            )
            params_dict["DIST_OPTIONAL"] = float(
                request.form.get("dist_optional", params_dict.get("DIST_OPTIONAL", 0.3))
            )
            params_dict["DIST_MANDATORY"] = float(
                request.form.get("dist_mandatory", params_dict.get("DIST_MANDATORY", 0.3))
            )
            params_dict["DIST_ALTERNATIVE"] = float(
                request.form.get("dist_alternative", params_dict.get("DIST_ALTERNATIVE", 0.2))
            )
            params_dict["DIST_OR"] = _safe_float(request.form.get("dist_or"), params_dict.get("DIST_OR", 0.2))
            if "group_cardinality" in request.form:
                params_dict["DIST_GROUP_CARDINALITY"] = float(
                    request.form.get("dist_group_cardinality", params_dict.get("DIST_GROUP_CARDINALITY", 0.0))
                )
                params_dict["GROUP_CARDINALITY_MIN"] = int(
                    request.form.get("group_cardinality_min", params_dict.get("GROUP_CARDINALITY_MIN", 10))
                )
                params_dict["GROUP_CARDINALITY_MAX"] = int(
                    request.form.get("group_cardinality_max", params_dict.get("GROUP_CARDINALITY_MAX", 50))
                )
            else:
                params_dict["DIST_GROUP_CARDINALITY"] = 0.0

            session["params"] = params_dict
            clear_step_state(2)
            return redirect(url_for("generator.step1"))

        errors, values = validate_step2_form(request.form)
        if errors:
            return render_template("generator/step2.html", current_step=2, errors=errors, values=values)

        params_dict = session.get("params")
        if not params_dict:
            return redirect(url_for("generator.landing"))

        # Niveles de lenguaje
        params_dict["GROUP_CARDINALITY"] = "group_cardinality" in request.form
        params_dict["ARITHMETIC_LEVEL"] = "arithmetic_level" in request.form
        params_dict["TYPE_LEVEL"] = "type_level" in request.form
        params_dict["FEATURE_CARDINALITY"] = "feature_cardinality" in request.form
        params_dict["AGGREGATE_FUNCTIONS"] = "aggregate_functions" in request.form
        params_dict["STRING_CONSTRAINTS"] = "string_constraints" in request.form

        # Enforce level hierarchy: a minor is only on if its major is on.
        if not params_dict["ARITHMETIC_LEVEL"]:
            params_dict["FEATURE_CARDINALITY"] = False
            params_dict["AGGREGATE_FUNCTIONS"] = False
        if not params_dict["TYPE_LEVEL"]:
            params_dict["STRING_CONSTRAINTS"] = False

        # Drop orphan step3 probabilities when their feature is off. Avoids
        # stale values lingering in session if the user toggles a level after
        # having filled step3. Names match Params fields in the vendor
        # dataclass (note: PROB_SUM/PROB_SUBSTRACT are the arithmetic +/−,
        # while PROB_SUM_FUNCTION/PROB_AVG_FUNCTION are the aggregates).
        _ARITH_KEYS = [
            "PROB_SUM",
            "PROB_SUBSTRACT",
            "PROB_MULTIPLY",
            "PROB_DIVIDE",
            "PROB_EQUALS",
            "PROB_LESS",
            "PROB_GREATER",
            "PROB_LESS_EQUALS",
            "PROB_GREATER_EQUALS",
        ]
        _AGG_KEYS = ["PROB_SUM_FUNCTION", "PROB_AVG_FUNCTION"]
        _STR_KEYS = ["PROB_LEN_FUNCTION"]
        if not params_dict["ARITHMETIC_LEVEL"]:
            for k in _ARITH_KEYS + _AGG_KEYS:
                params_dict.pop(k, None)
        if not params_dict["AGGREGATE_FUNCTIONS"]:
            for k in _AGG_KEYS:
                params_dict.pop(k, None)
        if not params_dict["STRING_CONSTRAINTS"]:
            for k in _STR_KEYS:
                params_dict.pop(k, None)

        params_dict["MIN_FEATURES"] = int(request.form.get("num_features_min", 1))
        params_dict["MAX_FEATURES"] = int(request.form.get("num_features_max", 10))

        # Tree depth
        params_dict["MAX_TREE_DEPTH"] = int(request.form.get("max_tree_depth", 5))

        # Groups
        params_dict["DIST_OPTIONAL"] = _safe_float(request.form.get("dist_optional"), 0.7)
        params_dict["DIST_MANDATORY"] = _safe_float(request.form.get("dist_mandatory"), 0.2)
        params_dict["DIST_ALTERNATIVE"] = _safe_float(request.form.get("dist_alternative"), 0.0)
        params_dict["DIST_OR"] = _safe_float(request.form.get("dist_or"), 0.0)

        # Group cardinality
        if "group_cardinality" in request.form:
            params_dict["DIST_GROUP_CARDINALITY"] = _safe_float(request.form.get("dist_group_cardinality"), 0.0)
            params_dict["GROUP_CARDINALITY_MIN"] = int(request.form.get("group_cardinality_min", 1))
            params_dict["GROUP_CARDINALITY_MAX"] = int(request.form.get("group_cardinality_max", 6))
        else:
            params_dict["DIST_GROUP_CARDINALITY"] = 0.0
            params_dict["GROUP_CARDINALITY_MIN"] = params_dict.get("GROUP_CARDINALITY_MIN", 1)
            params_dict["GROUP_CARDINALITY_MAX"] = params_dict.get("GROUP_CARDINALITY_MAX", 6)

        # Feature cardinality (only persisted when the minor is on).
        if params_dict.get("FEATURE_CARDINALITY"):
            params_dict["PROB_FEATURE_CARDINALITY"] = _safe_float(request.form.get("prob_fc"), 0.05)
            params_dict["MIN_FEATURE_CARDINALITY"] = [int(request.form.get("min_feature_cardinality", 2))]
            params_dict["MAX_FEATURE_CARDINALITY"] = [int(request.form.get("max_feature_cardinality", 5))]
        else:
            params_dict["PROB_FEATURE_CARDINALITY"] = 0.0
            params_dict.pop("MIN_FEATURE_CARDINALITY", None)
            params_dict.pop("MAX_FEATURE_CARDINALITY", None)

        # Renormalise relation distributions so they sum to EXACTLY 1.0. The
        # client normaliser can leave residue (~1e-4) from float rounding, and
        # Params.__post_init__ enforces a 1e-6 tolerance.
        _dist_keys = [
            "DIST_OPTIONAL",
            "DIST_MANDATORY",
            "DIST_ALTERNATIVE",
            "DIST_OR",
            "DIST_GROUP_CARDINALITY",
        ]
        _dist_total = sum(params_dict[k] for k in _dist_keys)
        if _dist_total > 0:
            for k in _dist_keys:
                params_dict[k] = round(params_dict[k] / _dist_total, 6)
            params_dict[_dist_keys[-1]] += round(1.0 - sum(params_dict[k] for k in _dist_keys), 6)

        try:
            from fm_generator.FMGenerator.models.config import Params

            params = Params(**params_dict)
        except Exception as e:
            errors["global"] = str(e)
            return render_template(
                "generator/step2.html",
                current_step=2,
                errors=errors,
                values=values,
            )

        session["params"] = params.__dict__
        clear_step_state(2)
        return redirect(url_for("generator.step3"))

    # ✅ GET
    params_dict = session.get("params", {})

    values = {
        # Boolean is forced on (the generator always produces at least the
        # Boolean level). Everything else defaults to off.
        "boolean_level": True,
        "group_cardinality": params_dict.get("GROUP_CARDINALITY", False),
        "arithmetic_level": params_dict.get("ARITHMETIC_LEVEL", False),
        "feature_cardinality": params_dict.get("FEATURE_CARDINALITY", False),
        "aggregate_functions": params_dict.get("AGGREGATE_FUNCTIONS", False),
        "type_level": params_dict.get("TYPE_LEVEL", False),
        "string_constraints": params_dict.get("STRING_CONSTRAINTS", False),
        # features
        "num_features_min": params_dict.get("MIN_FEATURES", 10),
        "num_features_max": params_dict.get("MAX_FEATURES", 50),
        "max_tree_depth": params_dict.get("MAX_TREE_DEPTH", 5),
        # feature cardinality attach prob (aunque esté comentado en HTML, lo
        # dejo)
        "prob_fc": params_dict.get("PROB_FEATURE_CARDINALITY", 0.1),
        # groups
        "dist_optional": params_dict.get("DIST_OPTIONAL", 0.3),
        "dist_mandatory": params_dict.get("DIST_MANDATORY", 0.3),
        "dist_alternative": params_dict.get("DIST_ALTERNATIVE", 0.2),
        "dist_or": params_dict.get("DIST_OR", 0.2),
        # group cardinality
        "dist_group_cardinality": params_dict.get("DIST_GROUP_CARDINALITY", 0.0),
        "group_cardinality_min": params_dict.get("GROUP_CARDINALITY_MIN", 10),
        "group_cardinality_max": params_dict.get("GROUP_CARDINALITY_MAX", 50),
        # sum displays
        "rel_dist_total": "1.0000",
    }

    values = load_step_state(2, values)

    return render_template(
        "generator/step2.html",
        current_step=2,
        errors={},
        values=values,
    )


def validate_step3_form(form, max_features: int = 10000):

    errors = {}
    values = {}

    # 1) NÚMERO DE CONSTRAINTS
    min_constraints_val = form.get("num_constraints_min", "").strip()
    max_constraints_val = form.get("num_constraints_max", "").strip()

    try:
        min_constraints = int(min_constraints_val)
        if min_constraints < 1:
            errors["num_constraints_min"] = "Min. constraints must be at least 1."
    except Exception:
        min_constraints = None
        errors["num_constraints_min"] = "Min. constraints must be an integer."

    try:
        max_constraints = int(max_constraints_val)
        if max_constraints < 1:
            errors["num_constraints_max"] = "Max. constraints must be at least 1."
    except Exception:
        max_constraints = None
        errors["num_constraints_max"] = "Max. constraints must be an integer."

    if (
        "num_constraints_min" not in errors
        and "num_constraints_max" not in errors
        and min_constraints is not None
        and max_constraints is not None
        and min_constraints > max_constraints
    ):
        errors["num_constraints_max"] = "Max. constraints must be greater than or equal to Min. constraints."

    # 2) EXTRA CONSTRAINT REPRESENTATIVENESS
    extra_constraint_repr_val = form.get("extra_constraint_repr", "").strip()
    vars_per_ctc_max_val = form.get("vars_per_ctc_max", "").strip()

    try:
        extra_constraint_repr = int(extra_constraint_repr_val)
    except Exception:
        extra_constraint_repr = None
        errors["extra_constraint_repr"] = "Must be an integer."
    try:
        vars_per_ctc_max = int(vars_per_ctc_max_val)
        if vars_per_ctc_max < 1:
            errors["vars_per_ctc_max"] = "Max. vars per constraint must be at least 1."
    except Exception:
        vars_per_ctc_max = None
        if "vars_per_ctc_max" not in errors:
            errors["vars_per_ctc_max"] = "Max. vars per constraint must be an integer."

    if extra_constraint_repr is not None and vars_per_ctc_max is not None:
        if extra_constraint_repr < 1:
            errors["extra_constraint_repr"] = "Must be an integer ≥ 1."
        elif extra_constraint_repr > vars_per_ctc_max:
            errors["extra_constraint_repr"] = "Must be less than or equal to max variables per constraint."

    # 3) VARIABLES POR CONSTRAINT
    try:
        vars_per_ctc_min = int(form.get("vars_per_ctc_min", "").strip())
        if vars_per_ctc_min < 1:
            errors["vars_per_ctc_min"] = "Min. vars per constraint must be at least 1."
    except Exception:
        vars_per_ctc_min = None
        errors["vars_per_ctc_min"] = "Min. vars per constraint must be an integer."

    vars_per_ctc_max_is_int = isinstance(vars_per_ctc_max, int)
    if vars_per_ctc_max_is_int:
        if vars_per_ctc_max > max_features:
            errors["vars_per_ctc_max"] = "Max. vars per constraint cannot exceed max number of features."

    if (
        ("vars_per_ctc_min" not in errors)
        and ("vars_per_ctc_max" not in errors)
        and vars_per_ctc_min is not None
        and vars_per_ctc_max_is_int
    ):
        if vars_per_ctc_min > vars_per_ctc_max:
            errors["vars_per_ctc_max"] = "Max. vars per constraint must be greater than or equal to Min."

    # 4) BOOLEAN LEVEL CONSTRAINTS
    try:
        prob_not = _safe_float(form.get("prob_not"), "0")
        if not (0.0 <= prob_not <= 1.0):
            errors["prob_not"] = "Value must be between 0 and 1."
    except Exception:
        errors["prob_not"] = "Value must be a decimal between 0 and 1."
        prob_not = 0.0

    try:
        prob_and = _safe_float(form.get("prob_and"), "0")
        prob_or = _safe_float(form.get("prob_or"), "0")
        prob_implies = _safe_float(form.get("prob_implies"), "0")
        prob_equiv = _safe_float(form.get("prob_equiv"), "0")
    except Exception:
        for f in ["prob_and", "prob_or", "prob_implies", "prob_equiv"]:
            if f not in errors:
                errors[f] = "Value must be a decimal between 0 and 1."
        prob_and = prob_or = prob_implies = prob_equiv = 0.0

    prob_sum_boolean = prob_and + prob_or + prob_implies + prob_equiv
    if abs(prob_sum_boolean - 1.0) > 0.001:
        for f in ["prob_and", "prob_or", "prob_implies", "prob_equiv"]:
            if f not in errors:
                errors[f] = "The sum of AND, OR, ⇒ and ⇔ must be exactly 1.0."
        errors["boolop_sum"] = f"Current sum: {prob_sum_boolean:.4f}. The total must be 1.0."
    values["boolop_sum"] = f"{prob_sum_boolean:.4f}"

    # 6) ARITHMETIC LEVEL + AGGREGATE FUNCTIONS
    arithmetic_level_checked = form.get("arithmetic_level") in [
        "on",
        "true",
        "1",
        True,
    ]

    aggregate_functions_checked = form.get("aggregate_functions") in [
        "on",
        "true",
        "1",
        True,
    ]

    if arithmetic_level_checked:
        try:
            prob_plus = _safe_float(form.get("prob_plus"), "0")
            prob_minus = _safe_float(form.get("prob_minus"), "0")
            prob_times = _safe_float(form.get("prob_times"), "0")
            prob_div = _safe_float(form.get("prob_div"), "0")
        except Exception:
            for f in ["prob_plus", "prob_minus", "prob_times", "prob_div"]:
                if f not in errors:
                    errors[f] = "Value must be a decimal between 0 and 1."
            prob_plus = prob_minus = prob_times = prob_div = 0.0

        if aggregate_functions_checked:
            try:
                prob_sum = _safe_float(form.get("prob_sum"), "0")
                prob_avg = _safe_float(form.get("prob_avg"), "0")
            except Exception:
                for f in ["prob_sum", "prob_avg"]:
                    if f not in errors:
                        errors[f] = "Value must be a decimal between 0 and 1."
                prob_sum = prob_avg = 0.0
        else:
            prob_sum = prob_avg = 0.0

        arithmetic_sum = prob_plus + prob_minus + prob_times + prob_div
        arithmetic_fields = ["prob_plus", "prob_minus", "prob_times", "prob_div"]
        agg_fields = ["prob_sum", "prob_avg"]

        if aggregate_functions_checked:
            arithmetic_sum += prob_sum + prob_avg
            fields_to_check = arithmetic_fields + agg_fields
        else:
            fields_to_check = arithmetic_fields

        if abs(arithmetic_sum - 1.0) > 0.001:
            for f in fields_to_check:
                if f not in errors:
                    errors[f] = "The sum of Arithmetic level constraints{} must be exactly 1.0.".format(
                        " (including aggregate functions)" if aggregate_functions_checked else ""
                    )
            errors["arithmetic_sum"] = f"Current sum: {arithmetic_sum:.4f}. The total must be 1.0."

        values["arithmetic_sum"] = f"{arithmetic_sum:.4f}"
    else:
        values["arithmetic_sum"] = "1.0000"

    # 7) COMPARISON OPERATORS (solo si Arithmetic level está activo)
    if arithmetic_level_checked:
        try:
            prob_eq = _safe_float(form.get("prob_eq"), "0")
            prob_lt = _safe_float(form.get("prob_lt"), "0")
            prob_gt = _safe_float(form.get("prob_gt"), "0")
            prob_leq = _safe_float(form.get("prob_leq"), "0")
            prob_geq = _safe_float(form.get("prob_geq"), "0")
        except Exception:
            for f in ["prob_eq", "prob_lt", "prob_gt", "prob_leq", "prob_geq"]:
                if f not in errors:
                    errors[f] = "Value must be a decimal between 0 and 1."
            prob_eq = prob_lt = prob_gt = prob_leq = prob_geq = 0.0

        cmp_sum = prob_eq + prob_lt + prob_gt + prob_leq + prob_geq
        if abs(cmp_sum - 1.0) > 0.001:
            for f in ["prob_eq", "prob_lt", "prob_gt", "prob_leq", "prob_geq"]:
                if f not in errors:
                    errors[f] = "The sum of comparison operators must be exactly 1.0."
            errors["cmp_sum"] = f"Current sum: {cmp_sum:.4f}. The total must be 1.0."

        values["cmp_sum"] = f"{cmp_sum:.4f}"
    else:
        values["cmp_sum"] = "1.0000"

    # 8) TYPE LEVEL / STRING CONSTRAINTS
    type_level_checked = form.get("type_level") in ["on", "true", "1", True]
    string_constraints_checked = form.get("string_constraints") in [
        "on",
        "true",
        "1",
        True,
    ]

    if string_constraints_checked and type_level_checked:
        try:
            prob_len = _safe_float(form.get("prob_len"), "0")
            if not (0.0 <= prob_len <= 1.0):
                errors["prob_len"] = "Value must be between 0 and 1."
        except Exception:
            errors["prob_len"] = "Value must be a decimal between 0 and 1."

    # 9) GUARDAR TODOS LOS VALORES PARA REPINTAR EL FORMULARIO
    for k in form:
        values[k] = form[k]

    return errors, values


@generator_bp.route("/generator/random/step3", methods=["GET", "POST"])
def step3():
    params_dict = session.get("params")
    if not params_dict:
        return redirect(url_for("generator.landing"))

    if request.method == "POST":
        nav = request.form.get("nav", "next")

        save_step_state(3, request.form, checkbox_fields=["aggregate_functions", "type_level", "string_constraints"])

        if nav == "prev":
            params_dict = session.get("params", {}) or {}

            params_dict["MIN_CONSTRAINTS"] = int(
                request.form.get("num_constraints_min", params_dict.get("MIN_CONSTRAINTS", 1))
            )
            params_dict["MAX_CONSTRAINTS"] = int(
                request.form.get("num_constraints_max", params_dict.get("MAX_CONSTRAINTS", 10))
            )
            # EXTRA_CONSTRAINT_REPRESENTATIVENESS is typed as float in the
            # vendor dataclass (default 0.5) but the form treats it as an int
            # count, so coerce via float to tolerate either shape.
            _ecr_raw = request.form.get(
                "extra_constraint_repr",
                params_dict.get("EXTRA_CONSTRAINT_REPRESENTATIVENESS", 1),
            )
            try:
                params_dict["EXTRA_CONSTRAINT_REPRESENTATIVENESS"] = max(1, int(float(_ecr_raw)))
            except (TypeError, ValueError):
                params_dict["EXTRA_CONSTRAINT_REPRESENTATIVENESS"] = 1
            params_dict["MIN_VARS_PER_CONSTRAINT"] = int(
                request.form.get("vars_per_ctc_min", params_dict.get("MIN_VARS_PER_CONSTRAINT", 1))
            )
            max_feats = int(params_dict.get("MAX_FEATURES", 10000))
            params_dict["MAX_VARS_PER_CONSTRAINT"] = min(
                int(
                    request.form.get(
                        "vars_per_ctc_max",
                        params_dict.get("MAX_VARS_PER_CONSTRAINT", 10),
                    )
                ),
                max_feats,
            )
            params_dict["PROB_NOT"] = _safe_float(request.form.get("prob_not"), params_dict.get("PROB_NOT", 0.3))
            params_dict["PROB_AND"] = _safe_float(request.form.get("prob_and"), params_dict.get("PROB_AND", 0.7))
            params_dict["PROB_OR_CT"] = _safe_float(request.form.get("prob_or"), params_dict.get("PROB_OR_CT", 0.1))
            params_dict["PROB_IMPLICATION"] = float(
                request.form.get("prob_implies", params_dict.get("PROB_IMPLICATION", 0.1))
            )
            params_dict["PROB_EQUIVALENCE"] = float(
                request.form.get("prob_equiv", params_dict.get("PROB_EQUIVALENCE", 0.1))
            )

            params_dict["PROB_SUM_FUNCTION"] = float(
                request.form.get("prob_sum", params_dict.get("PROB_SUM_FUNCTION", 0.0))
            )
            params_dict["PROB_AVG_FUNCTION"] = float(
                request.form.get("prob_avg", params_dict.get("PROB_AVG_FUNCTION", 0.0))
            )

            params_dict["PROB_SUM"] = _safe_float(request.form.get("prob_plus"), params_dict.get("PROB_SUM", 0.7))
            params_dict["PROB_SUBSTRACT"] = _safe_float(
                request.form.get("prob_minus"), params_dict.get("PROB_SUBSTRACT", 0.2)
            )
            params_dict["PROB_MULTIPLY"] = _safe_float(
                request.form.get("prob_times"), params_dict.get("PROB_MULTIPLY", 0.1)
            )
            params_dict["PROB_DIVIDE"] = _safe_float(request.form.get("prob_div"), params_dict.get("PROB_DIVIDE", 0.0))

            arithmetic_level_enabled = bool(params_dict.get("ARITHMETIC_LEVEL", False))

            if arithmetic_level_enabled:
                params_dict["PROB_EQUALS"] = _safe_float(
                    request.form.get("prob_eq"), params_dict.get("PROB_EQUALS", 0.1)
                )
                params_dict["PROB_LESS"] = _safe_float(request.form.get("prob_lt"), params_dict.get("PROB_LESS", 0.2))
                params_dict["PROB_GREATER"] = _safe_float(
                    request.form.get("prob_gt"), params_dict.get("PROB_GREATER", 0.7)
                )
                params_dict["PROB_LESS_EQUALS"] = _safe_float(
                    request.form.get("prob_leq"), params_dict.get("PROB_LESS_EQUALS", 0.0)
                )
                params_dict["PROB_GREATER_EQUALS"] = _safe_float(
                    request.form.get("prob_geq"), params_dict.get("PROB_GREATER_EQUALS", 0.0)
                )
            else:
                params_dict["PROB_EQUALS"] = 0.0
                params_dict["PROB_LESS"] = 0.0
                params_dict["PROB_GREATER"] = 0.0
                params_dict["PROB_LESS_EQUALS"] = 0.0
                params_dict["PROB_GREATER_EQUALS"] = 0.0

            type_level_enabled = bool(params_dict.get("TYPE_LEVEL", False))
            string_constraints_enabled = bool(params_dict.get("STRING_CONSTRAINTS", False))

            if type_level_enabled and string_constraints_enabled:
                params_dict["PROB_LEN_FUNCTION"] = _safe_float(
                    request.form.get("prob_len"),
                    params_dict.get("PROB_LEN_FUNCTION", 0.7),
                )
            else:
                params_dict["PROB_LEN_FUNCTION"] = 0.0
            session["params"] = params_dict
            clear_step_state(3)
            return redirect(url_for("generator.step2"))

        # Extraer max_features de params_dict
        max_feats = params_dict.get("MAX_FEATURES", 10000)

        errors, values = validate_step3_form(request.form, max_feats)

        values["arithmetic_level"] = "arithmetic_level" in request.form
        values["aggregate_functions"] = "aggregate_functions" in request.form
        values["type_level"] = "type_level" in request.form
        values["string_constraints"] = "string_constraints" in request.form

        if errors:
            return render_template("generator/step3.html", current_step=3, errors=errors, values=values)

        # Guardar campos en params_dict
        params_dict["MIN_CONSTRAINTS"] = int(request.form.get("num_constraints_min", 1))
        params_dict["MAX_CONSTRAINTS"] = int(request.form.get("num_constraints_max", 10))
        params_dict["EXTRA_CONSTRAINT_REPRESENTATIVENESS"] = int(request.form.get("extra_constraint_repr", 1))
        params_dict["MIN_VARS_PER_CONSTRAINT"] = int(request.form.get("vars_per_ctc_min", 1))

        max_feats = int(params_dict.get("MAX_FEATURES", 10000))
        params_dict["MAX_VARS_PER_CONSTRAINT"] = min(int(request.form.get("vars_per_ctc_max", 1)), max_feats)

        # Boolean level
        params_dict["PROB_NOT"] = _safe_float(request.form.get("prob_not"), 0.3)
        params_dict["PROB_AND"] = _safe_float(request.form.get("prob_and"), 0.7)
        params_dict["PROB_OR_CT"] = _safe_float(request.form.get("prob_or"), 0.1)
        params_dict["PROB_IMPLICATION"] = _safe_float(request.form.get("prob_implies"), 0.1)
        params_dict["PROB_EQUIVALENCE"] = _safe_float(request.form.get("prob_equiv"), 0.1)

        arithmetic_level_enabled = bool(params_dict.get("ARITHMETIC_LEVEL", False))
        aggregate_functions_enabled = bool(params_dict.get("AGGREGATE_FUNCTIONS", False))

        if arithmetic_level_enabled:
            params_dict["PROB_SUM"] = _safe_float(request.form.get("prob_plus"), 0.7)
            params_dict["PROB_SUBSTRACT"] = _safe_float(request.form.get("prob_minus"), 0.2)
            params_dict["PROB_MULTIPLY"] = _safe_float(request.form.get("prob_times"), 0.1)
            params_dict["PROB_DIVIDE"] = _safe_float(request.form.get("prob_div"), 0.0)

            if aggregate_functions_enabled:
                params_dict["PROB_SUM_FUNCTION"] = _safe_float(request.form.get("prob_sum"), 0.0)
                params_dict["PROB_AVG_FUNCTION"] = _safe_float(request.form.get("prob_avg"), 0.0)
            else:
                params_dict["PROB_SUM_FUNCTION"] = 0.0
                params_dict["PROB_AVG_FUNCTION"] = 0.0
        else:
            params_dict["PROB_SUM"] = 0.0
            params_dict["PROB_SUBSTRACT"] = 0.0
            params_dict["PROB_MULTIPLY"] = 0.0
            params_dict["PROB_DIVIDE"] = 0.0
            params_dict["PROB_SUM_FUNCTION"] = 0.0
            params_dict["PROB_AVG_FUNCTION"] = 0.0

        # Comparison operators
        if arithmetic_level_enabled:
            params_dict["PROB_EQUALS"] = _safe_float(request.form.get("prob_eq"), 0.1)
            params_dict["PROB_LESS"] = _safe_float(request.form.get("prob_lt"), 0.2)
            params_dict["PROB_GREATER"] = _safe_float(request.form.get("prob_gt"), 0.7)
            params_dict["PROB_LESS_EQUALS"] = _safe_float(request.form.get("prob_leq"), 0.0)
            params_dict["PROB_GREATER_EQUALS"] = _safe_float(request.form.get("prob_geq"), 0.0)
        else:
            params_dict["PROB_EQUALS"] = 0.0
            params_dict["PROB_LESS"] = 0.0
            params_dict["PROB_GREATER"] = 0.0
            params_dict["PROB_LESS_EQUALS"] = 0.0
            params_dict["PROB_GREATER_EQUALS"] = 0.0

        # Type level
        type_level_enabled = bool(params_dict.get("TYPE_LEVEL", False))
        string_constraints_enabled = bool(params_dict.get("STRING_CONSTRAINTS", False))

        if type_level_enabled and string_constraints_enabled:
            params_dict["PROB_LEN_FUNCTION"] = _safe_float(request.form.get("prob_len"), 0.7)
        else:
            params_dict["PROB_LEN_FUNCTION"] = 0.0

        # Renormalise the Boolean-connective probabilities to sum EXACTLY 1.0.
        # Params.__post_init__ enforces a 1e-6 tolerance; the form-side
        # normaliser rounds to 4 decimals, which can leave residue.
        _bool_keys = [
            "PROB_AND",
            "PROB_OR_CT",
            "PROB_IMPLICATION",
            "PROB_EQUIVALENCE",
        ]
        _bool_total = sum(params_dict[k] for k in _bool_keys)
        if _bool_total > 0:
            for k in _bool_keys:
                params_dict[k] = round(params_dict[k] / _bool_total, 6)
            params_dict[_bool_keys[-1]] += round(1.0 - sum(params_dict[k] for k in _bool_keys), 6)

        # En step3 solo guardamos el estado; no reconstruimos Params aquí
        # porque params_dict puede contener todavía datos del step4.
        session["params"] = params_dict
        clear_step_state(3)
        return redirect(url_for("generator.step4"))

    wizard = session.get("wizard", {})
    # significa: el usuario ya pasó por step3 y guardamos estado
    has_step3_saved = "3" in wizard

    max_feats = int(params_dict.get("MAX_FEATURES", 1000))

    # See note in the "prev" branch: the vendor default for this field is
    # 0.5 (float), but the UI expects an int >= 1.
    try:
        _ecr_default = max(1, int(float(params_dict.get("EXTRA_CONSTRAINT_REPRESENTATIVENESS", 1))))
    except (TypeError, ValueError):
        _ecr_default = 1

    default_values = {
        "num_constraints_min": params_dict.get("MIN_CONSTRAINTS", 1),
        "num_constraints_max": params_dict.get("MAX_CONSTRAINTS", 10),
        "extra_constraint_repr": _ecr_default,
        "vars_per_ctc_min": params_dict.get("MIN_VARS_PER_CONSTRAINT", 1),
        # 👇 importantísimo: que el default nunca supere max_feats
        "vars_per_ctc_max": min(int(params_dict.get("MAX_VARS_PER_CONSTRAINT", 10)), max_feats),
        # para mostrarlo en el template
        "max_features": max_feats,
        "boolop_sum": "1.0000",
        "arithmetic_sum": "1.0000",
        "cmp_sum": "1.0000",
        "arithmetic_level": params_dict.get("ARITHMETIC_LEVEL", False),
        "aggregate_functions": params_dict.get("AGGREGATE_FUNCTIONS", False),
        "type_level": params_dict.get("TYPE_LEVEL", False),
        "string_constraints": params_dict.get("STRING_CONSTRAINTS", False),
    }

    # Boolean level (puedes mantener params_dict o poner tus defaults fijos
    # igual)
    default_values.update(
        {
            "prob_not": params_dict.get("PROB_NOT", 0.3),
            "prob_and": params_dict.get("PROB_AND", 0.7),
            "prob_or": params_dict.get("PROB_OR_CT", 0.1),
            "prob_implies": params_dict.get("PROB_IMPLICATION", 0.1),
            "prob_equiv": params_dict.get("PROB_EQUIVALENCE", 0.1),
        }
    )

    # Aquí está la clave:
    if has_step3_saved:
        # si ya hay estado guardado, usa lo que haya en params_dict (o
        # directamente load_step_state luego)
        default_values.update(
            {
                "prob_plus": params_dict.get("PROB_SUM", STEP3_UI_DEFAULTS["prob_plus"]),
                "prob_minus": params_dict.get("PROB_SUBSTRACT", STEP3_UI_DEFAULTS["prob_minus"]),
                "prob_times": params_dict.get("PROB_MULTIPLY", STEP3_UI_DEFAULTS["prob_times"]),
                "prob_div": params_dict.get("PROB_DIVIDE", STEP3_UI_DEFAULTS["prob_div"]),
                "prob_sum": params_dict.get("PROB_SUM_FUNCTION", STEP3_UI_DEFAULTS["prob_sum"]),
                "prob_avg": params_dict.get("PROB_AVG_FUNCTION", STEP3_UI_DEFAULTS["prob_avg"]),
                "prob_eq": params_dict.get("PROB_EQUALS", STEP3_UI_DEFAULTS["prob_eq"]),
                "prob_lt": params_dict.get("PROB_LESS", STEP3_UI_DEFAULTS["prob_lt"]),
                "prob_gt": params_dict.get("PROB_GREATER", STEP3_UI_DEFAULTS["prob_gt"]),
                "prob_leq": params_dict.get("PROB_LESS_EQUALS", STEP3_UI_DEFAULTS["prob_leq"]),
                "prob_geq": params_dict.get("PROB_GREATER_EQUALS", STEP3_UI_DEFAULTS["prob_geq"]),
                "prob_len": (
                    params_dict.get("PROB_LEN_FUNCTION", STEP3_UI_DEFAULTS["prob_len"])
                    if params_dict.get("TYPE_LEVEL", False) and params_dict.get("STRING_CONSTRAINTS", False)
                    else 0.0
                ),
            }
        )
    else:
        # primera vez que entras a step3: IGNORA params_dict para estos campos
        default_values.update(STEP3_UI_DEFAULTS)
        if not (params_dict.get("TYPE_LEVEL", False) and params_dict.get("STRING_CONSTRAINTS", False)):
            default_values["prob_len"] = 0.0

    values = load_step_state(3, default_values)

    # Estos flags deben venir SIEMPRE del step2 (params), no de un estado
    # viejo del wizard
    values["arithmetic_level"] = params_dict.get("ARITHMETIC_LEVEL", False)
    values["aggregate_functions"] = params_dict.get("AGGREGATE_FUNCTIONS", False)
    values["type_level"] = params_dict.get("TYPE_LEVEL", False)
    values["string_constraints"] = params_dict.get("STRING_CONSTRAINTS", False)

    # si el usuario tenía guardado en wizard un número mayor, lo capamos
    try:
        values["vars_per_ctc_max"] = str(min(int(values.get("vars_per_ctc_max", max_feats)), max_feats))
    except Exception:
        values["vars_per_ctc_max"] = str(max_feats)

    # aseguramos que el template lo tenga siempre
    values["max_features"] = max_feats

    return render_template(
        "generator/step3.html",
        current_step=3,
        errors={},
        values=values,
    )


def validate_step4_form(form, params_dict=None):
    errors = {}
    values = {}
    params_dict = params_dict or {}

    arithmetic_level_enabled = bool(params_dict.get("ARITHMETIC_LEVEL", False))
    type_level_enabled = bool(params_dict.get("TYPE_LEVEL", False))
    string_constraints_enabled = bool(params_dict.get("STRING_CONSTRAINTS", False))

    random_checked = "random_attributes" in form
    values["random_attributes"] = random_checked

    if random_checked:
        min_attr_val = form.get("min_attributes", "").strip()
        max_attr_val = form.get("max_attributes", "").strip()

        try:
            min_attr = int(min_attr_val)
            if not (1 <= min_attr <= 1000):
                errors["min_attributes"] = "Min. attributes must be between 1 and 1000."
        except Exception:
            min_attr = None
            errors["min_attributes"] = "Min. attributes must be an integer."

        try:
            max_attr = int(max_attr_val)
            if not (1 <= max_attr <= 1000):
                errors["max_attributes"] = "Max. attributes must be between 1 and 1000."
        except Exception:
            max_attr = None
            errors["max_attributes"] = "Max. attributes must be an integer."

        if (
            "min_attributes" not in errors
            and "max_attributes" not in errors
            and min_attr is not None
            and max_attr is not None
            and min_attr > max_attr
        ):
            errors["max_attributes"] = "Max. attributes must be greater than or equal to Min."

        values["min_attributes"] = min_attr_val
        values["max_attributes"] = max_attr_val

    else:
        values["min_attributes"] = ""
        values["max_attributes"] = ""

        # Detectar cuántas tarjetas hay, buscando todos los attr_name_*
        attr_names = []
        idx = 0
        while True:
            key = f"attr_name_{idx}"
            if key in form:
                attr_names.append(form.get(key))
                idx += 1
            else:
                break

        attr_types = [form.get(f"attr_type_{i}", "").strip() for i in range(len(attr_names))]

        # Validar nombre del atributo
        for i in range(len(attr_names)):
            name = (form.get(f"attr_name_{i}", "") or "").strip()
            if not name:
                errors[f"attr_name_{i}"] = "Attribute name is required."

        # Validar use_in_constraints según el tipo y los levels activos
        for i in range(len(attr_names)):
            type_lc = (form.get(f"attr_type_{i}", "") or "").strip().lower()
            use_in_constraints = form.get(f"attr_use_in_constraints_{i}") == "on"

            if not use_in_constraints:
                continue

            if type_lc == "boolean":
                pass
            elif type_lc in ("integer", "real"):
                if not arithmetic_level_enabled:
                    errors[f"attr_use_in_constraints_{i}"] = (
                        "Use in constraints is only available for Integer and "
                        "Real attributes when Arithmetic level is enabled."
                    )
            elif type_lc == "string":
                if not (type_level_enabled and string_constraints_enabled):
                    errors[f"attr_use_in_constraints_{i}"] = (
                        "Use in constraints is only available for String attributes when "
                        "Type level and String constraints are enabled."
                    )

        # Validar por cada atributo
        for i, t in enumerate(attr_types):
            t_lc = t.lower()

            attach_prob_val = (form.get(f"attr_attach_prob_{i}", "") or "").strip()
            if not attach_prob_val:
                errors[f"attr_attach_prob_{i}"] = "Attach probability is required."
            else:
                try:
                    attach_prob = float(attach_prob_val)
                    if attach_prob < 0:
                        errors[f"attr_attach_prob_{i}"] = "Attach probability cannot be negative."
                    elif attach_prob > 1:
                        errors[f"attr_attach_prob_{i}"] = "Attach probability cannot be greater than 1."
                except Exception:
                    errors[f"attr_attach_prob_{i}"] = "Attach probability must be a number between 0 and 1."

            if t_lc == "boolean":
                true_checked = form.get(f"attr_value_true_{i}") is not None
                false_checked = form.get(f"attr_value_false_{i}") is not None
                if not true_checked and not false_checked:
                    errors[f"attr_value_bool_{i}"] = (
                        "At least one value (True or False) must be selected for Boolean attribute."
                    )

            elif t_lc == "integer":
                min_val = form.get(f"attr_min_value_{i}", "").strip()
                max_val = form.get(f"attr_max_value_{i}", "").strip()

                if not min_val or not max_val:
                    errors[f"attr_minmax_{
                        i}"] = "Min and Max values are required."
                else:
                    try:
                        min_i = int(min_val)
                        max_i = int(max_val)
                        if min_i > max_i:
                            errors[f"attr_minmax_{
                                i}"] = "Min cannot be greater than Max."
                    except Exception:
                        errors[f"attr_minmax_{
                            i}"] = "Min and Max must be integers."

            elif t_lc == "real":
                min_val = form.get(f"attr_min_value_{i}", "").strip()
                max_val = form.get(f"attr_max_value_{i}", "").strip()

                if not min_val or not max_val:
                    errors[f"attr_minmax_{
                        i}"] = "Min and Max values are required."
                else:
                    try:
                        min_f = float(min_val)
                        max_f = float(max_val)
                        if min_f > max_f:
                            errors[f"attr_minmax_{
                                i}"] = "Min cannot be greater than Max."
                    except Exception:
                        errors[f"attr_minmax_{
                            i}"] = "Min and Max must be numbers."

            elif t_lc == "string":
                min_val = form.get(f"attr_min_value_{i}", "").strip()
                max_val = form.get(f"attr_max_value_{i}", "").strip()

                if not min_val or not max_val:
                    errors[f"attr_minmax_{
                        i}"] = "Min and Max values are required."
                else:
                    try:
                        min_len = int(min_val)
                        max_len = int(max_val)
                        if min_len < 0 or max_len < 0:
                            errors[f"attr_minmax_{
                                i}"] = "Min and Max must be non-negative integers."
                        elif min_len > max_len:
                            errors[f"attr_minmax_{
                                i}"] = "Min cannot be greater than Max."
                    except Exception:
                        errors[f"attr_minmax_{
                            i}"] = "Min and Max must be integers."

        # Guardar campos en values para repintar el formulario
        for k in form:
            values[k] = form[k]

    return errors, values


def _collect_step4_attributes(form, params_dict):
    """Parse the dynamic attribute rows from the step4 form.

    Returns the three lists that land in params_dict: ATTRIBUTES_LIST,
    ATTRIBUTE_ATTACH_PROBS, ATTRIBUTE_IN_CONSTRAINTS. Only called when
    RANDOM_ATTRIBUTES is off.
    """
    attr_count = 0
    while f"attr_name_{attr_count}" in form:
        attr_count += 1

    attributes_data = []
    attach_probs = []
    in_constraints = []

    for i in range(attr_count):
        name = form.get(f"attr_name_{i}", "")
        type_ = form.get(f"attr_type_{i}", "").strip().lower()

        attach_prob = _safe_float(form.get(f"attr_attach_prob_{i}"), 1.0)

        raw_use = form.get(f"attr_use_in_constraints_{i}") == "on"
        if type_ == "boolean":
            use_in_constraints = raw_use
        elif type_ in ("integer", "real"):
            use_in_constraints = raw_use and params_dict.get("ARITHMETIC_LEVEL", False)
        elif type_ == "string":
            use_in_constraints = (
                raw_use and params_dict.get("TYPE_LEVEL", False) and params_dict.get("STRING_CONSTRAINTS", False)
            )
        else:
            use_in_constraints = False

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
                "use_in_constraints": use_in_constraints,
            }
        elif type_ in ("integer", "real", "string"):
            attr_dict = {
                "name": name,
                "type": type_.capitalize(),
                "min_value": form.get(f"attr_min_value_{i}", None),
                "max_value": form.get(f"attr_max_value_{i}", None),
                "attach_probability": attach_prob,
                "use_in_constraints": use_in_constraints,
            }
        else:
            continue

        attributes_data.append(attr_dict)
        attach_probs.append(attach_prob)
        in_constraints.append(use_in_constraints)

    return attributes_data, attach_probs, in_constraints


def _apply_step4_form(params_dict, form):
    """Write the step4 form onto params_dict in place.

    Shared by both the forward-nav and the back-nav branches so the two
    paths can't drift apart.
    """
    random_attributes = "random_attributes" in form
    params_dict["RANDOM_ATTRIBUTES"] = random_attributes

    if random_attributes:
        params_dict["MIN_ATTRIBUTES"] = int(form.get("min_attributes", 1))
        params_dict["MAX_ATTRIBUTES"] = int(form.get("max_attributes", 5))
        params_dict["ATTRIBUTES_LIST"] = []
        params_dict["ATTRIBUTE_ATTACH_PROBS"] = []
        params_dict["ATTRIBUTE_IN_CONSTRAINTS"] = []
    else:
        attrs, probs, in_ctc = _collect_step4_attributes(form, params_dict)
        params_dict["MIN_ATTRIBUTES"] = None
        params_dict["MAX_ATTRIBUTES"] = None
        params_dict["ATTRIBUTES_LIST"] = attrs
        params_dict["ATTRIBUTE_ATTACH_PROBS"] = probs
        params_dict["ATTRIBUTE_IN_CONSTRAINTS"] = in_ctc


@generator_bp.route("/generator/random/step4", methods=["GET", "POST"])
def step4():
    if request.method == "POST":
        nav = request.form.get("nav", "next")
        save_step_state(4, request.form, checkbox_fields=["random_attributes"])

        params_dict = session.get("params", {}) or {}

        if nav == "prev":
            _apply_step4_form(params_dict, request.form)
            session["params"] = params_dict
            clear_step_state(4)
            return redirect(url_for("generator.step3"))

        if not params_dict:
            return redirect(url_for("generator.landing"))

        errors, values = validate_step4_form(request.form, params_dict)
        if errors:
            return render_template("generator/step4.html", current_step=4, errors=errors, values=values)

        _apply_step4_form(params_dict, request.form)
        session["params"] = params_dict
        clear_step_state(4)
        return redirect(url_for("generator.step5"))

    current_step = 4
    params_dict = session.get("params", {})

    default_values = {
        "random_attributes": params_dict.get("RANDOM_ATTRIBUTES", True),
        "min_attributes": params_dict.get("MIN_ATTRIBUTES", 1),
        "max_attributes": params_dict.get("MAX_ATTRIBUTES", 5),
        "attributes_list": params_dict.get("ATTRIBUTES_LIST", []),
    }

    values = load_step_state(4, default_values)

    return render_template(
        "generator/step4.html",
        current_step=current_step,
        errors={},
        values=values,
        arithmetic_level=params_dict.get("ARITHMETIC_LEVEL", False),
        type_level=params_dict.get("TYPE_LEVEL", False),
        string_constraints=params_dict.get("STRING_CONSTRAINTS", False),
    )


# Step 5 is the download page. Generation runs entirely in the browser via
# Pyodide (see app/modules/generator/assets/js/scripts.js — generateAndDownload).
# The server only renders the page; no feature models are produced or stored
# here.
@generator_bp.route("/generator/random/step5", methods=["GET", "POST"])
def step5():
    if request.method == "POST" and request.form.get("nav") == "prev":
        return redirect(url_for("generator.step4"))

    if not session.get("params"):
        return redirect(url_for("generator.landing"))

    return render_template("generator/step5.html", current_step=5)


@generator_bp.route("/generator/random/params-json", methods=["GET"])
def get_params_json():
    params = session.get("params")
    if not params:
        return jsonify({"error": "Params missing"}), 400
    return jsonify(params)
