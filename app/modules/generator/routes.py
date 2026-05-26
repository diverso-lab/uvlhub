"""Wizard routes — 6 steps, one clear decision per page.

    Step 1  Batch           num_models, seed, name_prefix
    Step 2  Language levels major + minor toggles (pure expressivity)
    Step 3  Feature tree    features/depth/relation dist + feat/group card
    Step 4  Constraints     counts, vars/ctc, CTC_DIST + prob distributions
    Step 5  Attributes      random/manual, DIST_BOOLEAN/INT/REAL/STRING
    Step 6  Output          ensure_satisfiable, filename suffixes, download

Each step only writes the fields it owns into ``session["params"]`` so
back-nav can't silently lose state from later steps, and every validator
is independent of the others.
"""

from flask import jsonify, redirect, render_template, request, session, url_for

from app.modules.generator import generator_bp
from app.modules.generator.services import (
    GeneratorService,
    clear_step_state,
    collect_manual_attributes,
    load_step_state,
    normalize_distribution,
    safe_float,
    save_step_state,
    apply_step2_levels,
    apply_step3_tree,
    apply_step4_constraints,
    apply_step5_attributes,
    apply_step6_output,
)
from app.modules.generator.validators import (
    validate_step1_form,
    validate_step2_form,
    validate_step3_form,
    validate_step4_form,
    validate_step5_form,
    validate_step6_form,
)

generator_service = GeneratorService()

TOTAL_STEPS = 6

STEP4_UI_DEFAULTS = {
    # Arithmetic (without aggregates)
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
    # String constraints
    "prob_len": 0.7,
}


# ─── Entry points ────────────────────────────────────────────────────────


@generator_bp.route("/generator", methods=["GET"])
@generator_bp.route("/generator/", methods=["GET"])
def landing():
    """Reset wizard state on every visit so a new run starts fresh."""
    session.pop("params", None)
    session.pop("wizard", None)
    return render_template("generator/landing.html")


@generator_bp.route("/generator/random", methods=["GET"])
@generator_bp.route("/generator/random/", methods=["GET"])
def random_entry():
    return redirect(url_for("generator.step1"))


@generator_bp.route("/generator/llm", methods=["GET"])
@generator_bp.route("/generator/llm/", methods=["GET"])
def llm():
    return render_template("generator/llm.html")


# ─── Step 1 · Batch ──────────────────────────────────────────────────────


@generator_bp.route("/generator/random/step1", methods=["GET", "POST"])
def step1():
    if request.method == "POST":
        errors, values = validate_step1_form(request.form)
        if errors:
            return render_template("generator/step1.html", current_step=1, errors=errors, values=values)
        # Persist ONLY the three fields step 1 owns. Earlier versions dumped
        # the whole Params dataclass (including every dataclass default)
        # into session, which made the sidebar summary display stale
        # "defaults" for steps the user hadn't reached yet. The wrapper
        # reconstructs Params(**dict) on the fly using its own defaults,
        # so the downstream flow doesn't need this pre-fill.
        p = session.get("params", {}) or {}
        try:
            p["NUM_MODELS"] = int(request.form.get("num_models_val"))
            p["SEED"] = int(request.form.get("seed"))
            p["NAME_PREFIX"] = request.form.get("name_prefix", "")
        except (TypeError, ValueError) as e:
            errors["global"] = str(e)
            return render_template(
                "generator/step1.html",
                current_step=1,
                errors=errors,
                values=request.form,
            )
        session["params"] = p
        clear_step_state(1)
        return redirect(url_for("generator.step2"))

    params_dict = session.get("params", {})
    values = {
        "num_models_val": params_dict.get("NUM_MODELS", 5),
        "seed": params_dict.get("SEED", 42),
        "name_prefix": params_dict.get("NAME_PREFIX", ""),
    }
    return render_template("generator/step1.html", current_step=1, errors={}, values=values)


# ─── Step 2 · Language levels ────────────────────────────────────────────


@generator_bp.route("/generator/random/step2", methods=["GET", "POST"])
def step2():
    if request.method == "POST":
        nav = request.form.get("nav", "next")
        save_step_state(
            2,
            request.form,
            checkbox_fields=[
                "boolean_level",
                "arithmetic_level",
                "type_level",
                "feature_cardinality",
                "aggregate_functions",
                "string_constraints",
                "group_cardinality",
            ],
        )
        params_dict = session.get("params", {}) or {}
        apply_step2_levels(params_dict, request.form)
        session["params"] = params_dict

        if nav == "prev":
            clear_step_state(2)
            return redirect(url_for("generator.step1"))

        errors, values = validate_step2_form(request.form)
        if errors:
            return render_template("generator/step2.html", current_step=2, errors=errors, values=values)
        clear_step_state(2)
        return redirect(url_for("generator.step3"))

    params_dict = session.get("params", {})
    values = {
        "boolean_level": True,
        "arithmetic_level": params_dict.get("ARITHMETIC_LEVEL", False),
        "type_level": params_dict.get("TYPE_LEVEL", False),
        "feature_cardinality": params_dict.get("FEATURE_CARDINALITY", False),
        "aggregate_functions": params_dict.get("AGGREGATE_FUNCTIONS", False),
        "string_constraints": params_dict.get("STRING_CONSTRAINTS", False),
        "group_cardinality": params_dict.get("GROUP_CARDINALITY", False),
    }
    values = load_step_state(2, values)
    return render_template("generator/step2.html", current_step=2, errors={}, values=values)


# ─── Step 3 · Feature tree ───────────────────────────────────────────────


@generator_bp.route("/generator/random/step3", methods=["GET", "POST"])
def step3():
    params_dict = session.get("params")
    if not params_dict:
        return redirect(url_for("generator.landing"))

    if request.method == "POST":
        nav = request.form.get("nav", "next")
        save_step_state(3, request.form, checkbox_fields=[])

        if nav == "prev":
            apply_step3_tree(params_dict, request.form)
            session["params"] = params_dict
            clear_step_state(3)
            return redirect(url_for("generator.step2"))

        errors, values = validate_step3_form(request.form, params_dict)
        values.update(
            {
                "arithmetic_level": params_dict.get("ARITHMETIC_LEVEL", False),
                "type_level": params_dict.get("TYPE_LEVEL", False),
                "feature_cardinality": params_dict.get("FEATURE_CARDINALITY", False),
                "aggregate_functions": params_dict.get("AGGREGATE_FUNCTIONS", False),
                "string_constraints": params_dict.get("STRING_CONSTRAINTS", False),
                "group_cardinality": params_dict.get("GROUP_CARDINALITY", False),
            }
        )
        if errors:
            return render_template("generator/step3.html", current_step=3, errors=errors, values=values)
        apply_step3_tree(params_dict, request.form)
        session["params"] = params_dict
        clear_step_state(3)
        return redirect(url_for("generator.step4"))

    values = {
        "num_features_min": params_dict.get("MIN_FEATURES", 10),
        "num_features_max": params_dict.get("MAX_FEATURES", 50),
        "max_tree_depth": params_dict.get("MAX_TREE_DEPTH", 5),
        "dist_optional": params_dict.get("DIST_OPTIONAL", 0.3),
        "dist_mandatory": params_dict.get("DIST_MANDATORY", 0.3),
        "dist_alternative": params_dict.get("DIST_ALTERNATIVE", 0.2),
        "dist_or": params_dict.get("DIST_OR", 0.2),
        "dist_group_cardinality": params_dict.get("DIST_GROUP_CARDINALITY", 0.0),
        "group_cardinality_min": params_dict.get("GROUP_CARDINALITY_MIN", 1),
        "group_cardinality_max": params_dict.get("GROUP_CARDINALITY_MAX", 6),
        "prob_fc": params_dict.get("PROB_FEATURE_CARDINALITY", 0.1),
        "min_feature_cardinality": (params_dict.get("MIN_FEATURE_CARDINALITY", [2]) or [2])[0],
        "max_feature_cardinality": (params_dict.get("MAX_FEATURE_CARDINALITY", [5]) or [5])[0],
        # Flags for gating the UI — must come from params (step2 truth).
        "arithmetic_level": params_dict.get("ARITHMETIC_LEVEL", False),
        "type_level": params_dict.get("TYPE_LEVEL", False),
        "feature_cardinality": params_dict.get("FEATURE_CARDINALITY", False),
        "aggregate_functions": params_dict.get("AGGREGATE_FUNCTIONS", False),
        "string_constraints": params_dict.get("STRING_CONSTRAINTS", False),
        "group_cardinality": params_dict.get("GROUP_CARDINALITY", False),
        "rel_dist_total": "1.0000",
    }
    values = load_step_state(3, values)
    return render_template("generator/step3.html", current_step=3, errors={}, values=values)


# ─── Step 4 · Constraints ────────────────────────────────────────────────


@generator_bp.route("/generator/random/step4", methods=["GET", "POST"])
def step4():
    params_dict = session.get("params")
    if not params_dict:
        return redirect(url_for("generator.landing"))

    if request.method == "POST":
        nav = request.form.get("nav", "next")
        save_step_state(4, request.form, checkbox_fields=[])

        if nav == "prev":
            apply_step4_constraints(params_dict, request.form)
            session["params"] = params_dict
            clear_step_state(4)
            return redirect(url_for("generator.step3"))

        max_feats = int(params_dict.get("MAX_FEATURES", 10000))
        errors, values = validate_step4_form(request.form, max_feats, params_dict)
        values["arithmetic_level"] = params_dict.get("ARITHMETIC_LEVEL", False)
        values["aggregate_functions"] = params_dict.get("AGGREGATE_FUNCTIONS", False)
        values["type_level"] = params_dict.get("TYPE_LEVEL", False)
        values["string_constraints"] = params_dict.get("STRING_CONSTRAINTS", False)
        if errors:
            return render_template("generator/step4.html", current_step=4, errors=errors, values=values)
        apply_step4_constraints(params_dict, request.form)
        session["params"] = params_dict
        clear_step_state(4)
        return redirect(url_for("generator.step5"))

    wizard = session.get("wizard", {})
    has_saved = "4" in wizard
    max_feats = int(params_dict.get("MAX_FEATURES", 1000))
    try:
        _ecr_default = max(1, int(float(params_dict.get("EXTRA_CONSTRAINT_REPRESENTATIVENESS", 1))))
    except (TypeError, ValueError):
        _ecr_default = 1

    defaults = {
        "num_constraints_min": params_dict.get("MIN_CONSTRAINTS", 1),
        "num_constraints_max": params_dict.get("MAX_CONSTRAINTS", 10),
        "extra_constraint_repr": _ecr_default,
        "vars_per_ctc_min": params_dict.get("MIN_VARS_PER_CONSTRAINT", 1),
        "vars_per_ctc_max": min(int(params_dict.get("MAX_VARS_PER_CONSTRAINT", 10)), max_feats),
        "max_features": max_feats,
        "boolop_sum": "1.0000",
        "arithmetic_sum": "1.0000",
        "cmp_sum": "1.0000",
        "ctc_dist_sum": "1.0000",
        "ctc_dist_boolean": params_dict.get("CTC_DIST_BOOLEAN", 0.7),
        "ctc_dist_integer": params_dict.get("CTC_DIST_INTEGER", 0.2),
        "ctc_dist_real": params_dict.get("CTC_DIST_REAL", 0.1),
        "ctc_dist_string": params_dict.get("CTC_DIST_STRING", 0.0),
        "arithmetic_level": params_dict.get("ARITHMETIC_LEVEL", False),
        "aggregate_functions": params_dict.get("AGGREGATE_FUNCTIONS", False),
        "type_level": params_dict.get("TYPE_LEVEL", False),
        "string_constraints": params_dict.get("STRING_CONSTRAINTS", False),
        "prob_not": params_dict.get("PROB_NOT", 0.3),
        "prob_and": params_dict.get("PROB_AND", 0.7),
        "prob_or": params_dict.get("PROB_OR_CT", 0.1),
        "prob_implies": params_dict.get("PROB_IMPLICATION", 0.1),
        "prob_equiv": params_dict.get("PROB_EQUIVALENCE", 0.1),
    }
    if has_saved:
        defaults.update(
            {
                "prob_plus": params_dict.get("PROB_SUM", STEP4_UI_DEFAULTS["prob_plus"]),
                "prob_minus": params_dict.get("PROB_SUBSTRACT", STEP4_UI_DEFAULTS["prob_minus"]),
                "prob_times": params_dict.get("PROB_MULTIPLY", STEP4_UI_DEFAULTS["prob_times"]),
                "prob_div": params_dict.get("PROB_DIVIDE", STEP4_UI_DEFAULTS["prob_div"]),
                "prob_sum": params_dict.get("PROB_SUM_FUNCTION", STEP4_UI_DEFAULTS["prob_sum"]),
                "prob_avg": params_dict.get("PROB_AVG_FUNCTION", STEP4_UI_DEFAULTS["prob_avg"]),
                "prob_eq": params_dict.get("PROB_EQUALS", STEP4_UI_DEFAULTS["prob_eq"]),
                "prob_lt": params_dict.get("PROB_LESS", STEP4_UI_DEFAULTS["prob_lt"]),
                "prob_gt": params_dict.get("PROB_GREATER", STEP4_UI_DEFAULTS["prob_gt"]),
                "prob_leq": params_dict.get("PROB_LESS_EQUALS", STEP4_UI_DEFAULTS["prob_leq"]),
                "prob_geq": params_dict.get("PROB_GREATER_EQUALS", STEP4_UI_DEFAULTS["prob_geq"]),
                "prob_len": (
                    params_dict.get("PROB_LEN_FUNCTION", STEP4_UI_DEFAULTS["prob_len"])
                    if params_dict.get("TYPE_LEVEL") and params_dict.get("STRING_CONSTRAINTS")
                    else 0.0
                ),
            }
        )
    else:
        defaults.update(STEP4_UI_DEFAULTS)
        if not (params_dict.get("TYPE_LEVEL") and params_dict.get("STRING_CONSTRAINTS")):
            defaults["prob_len"] = 0.0

    values = load_step_state(4, defaults)
    # Always trust params for level flags (never stale wizard state).
    values["arithmetic_level"] = params_dict.get("ARITHMETIC_LEVEL", False)
    values["aggregate_functions"] = params_dict.get("AGGREGATE_FUNCTIONS", False)
    values["type_level"] = params_dict.get("TYPE_LEVEL", False)
    values["string_constraints"] = params_dict.get("STRING_CONSTRAINTS", False)
    try:
        values["vars_per_ctc_max"] = str(min(int(values.get("vars_per_ctc_max", max_feats)), max_feats))
    except Exception:
        values["vars_per_ctc_max"] = str(max_feats)
    values["max_features"] = max_feats

    return render_template("generator/step4.html", current_step=4, errors={}, values=values)


# ─── Step 5 · Attributes ─────────────────────────────────────────────────


@generator_bp.route("/generator/random/step5", methods=["GET", "POST"])
def step5():
    params_dict = session.get("params")
    if not params_dict:
        return redirect(url_for("generator.landing"))

    if request.method == "POST":
        nav = request.form.get("nav", "next")
        save_step_state(5, request.form, checkbox_fields=["random_attributes"])

        if nav == "prev":
            apply_step5_attributes(params_dict, request.form)
            session["params"] = params_dict
            clear_step_state(5)
            return redirect(url_for("generator.step4"))

        errors, values = validate_step5_form(request.form, params_dict)
        if errors:
            return render_template(
                "generator/step5.html",
                current_step=5,
                errors=errors,
                values=values,
                arithmetic_level=params_dict.get("ARITHMETIC_LEVEL", False),
                type_level=params_dict.get("TYPE_LEVEL", False),
                string_constraints=params_dict.get("STRING_CONSTRAINTS", False),
            )
        apply_step5_attributes(params_dict, request.form)
        session["params"] = params_dict
        clear_step_state(5)
        return redirect(url_for("generator.step6"))

    defaults = {
        "random_attributes": params_dict.get("RANDOM_ATTRIBUTES", True),
        "min_attributes": params_dict.get("MIN_ATTRIBUTES", 1),
        "max_attributes": params_dict.get("MAX_ATTRIBUTES", 5),
        "attributes_list": params_dict.get("ATTRIBUTES_LIST", []),
        "dist_boolean": params_dict.get("DIST_BOOLEAN", 0.7),
        "dist_integer": params_dict.get("DIST_INTEGER", 0.1),
        "dist_real": params_dict.get("DIST_REAL", 0.1),
        "dist_string": params_dict.get("DIST_STRING", 0.1),
        "attr_dist_sum": "1.0000",
    }
    values = load_step_state(5, defaults)
    return render_template(
        "generator/step5.html",
        current_step=5,
        errors={},
        values=values,
        arithmetic_level=params_dict.get("ARITHMETIC_LEVEL", False),
        type_level=params_dict.get("TYPE_LEVEL", False),
        string_constraints=params_dict.get("STRING_CONSTRAINTS", False),
    )


# ─── Step 6 · Output + download ──────────────────────────────────────────


@generator_bp.route("/generator/random/step6", methods=["GET", "POST"])
def step6():
    params_dict = session.get("params")
    if not params_dict:
        return redirect(url_for("generator.landing"))

    if request.method == "POST":
        nav = request.form.get("nav", "next")
        save_step_state(
            6,
            request.form,
            checkbox_fields=[
                "ensure_satisfiable",
                "feature_count_suffix",
                "constraint_count_suffix",
            ],
        )
        apply_step6_output(params_dict, request.form)
        session["params"] = params_dict
        if nav == "prev":
            clear_step_state(6)
            return redirect(url_for("generator.step5"))
        # The actual model generation runs client-side in Pyodide once the
        # user clicks "Generate & download"; this POST just persists the
        # output options so params-json reflects them.
        clear_step_state(6)
        return redirect(url_for("generator.step6"))

    defaults = {
        # ENSURE_SATISFIABLE triggers up to 20 retries per model via pysat;
        # on big configurations that can multiply generation time 20×. Keep
        # it OFF by default and warn the user on the step 6 card.
        "ensure_satisfiable": params_dict.get("ENSURE_SATISFIABLE", False),
        "feature_count_suffix": params_dict.get("INCLUDE_FEATURE_COUNT_SUFFIX", False),
        "constraint_count_suffix": params_dict.get("INCLUDE_CONSTRAINT_COUNT_SUFFIX", False),
    }
    values = load_step_state(6, defaults)
    return render_template("generator/step6.html", current_step=6, errors={}, values=values)


# ─── Pyodide endpoint ────────────────────────────────────────────────────


@generator_bp.route("/generator/random/params-json", methods=["GET"])
def get_params_json():
    params = session.get("params")
    if not params:
        return jsonify({"error": "Params missing"}), 400
    return jsonify(params)


# Dispatch table for the live-summary endpoint so it stays in sync with
# the real step handlers. Each entry persists its step's form data onto
# a working copy of session["params"].
_DRAFT_PERSISTERS = {
    2: apply_step2_levels,
    3: apply_step3_tree,
    4: apply_step4_constraints,
    5: apply_step5_attributes,
    6: apply_step6_output,
}


@generator_bp.route("/generator/random/summary-refresh/<int:step>", methods=["POST"])
def refresh_summary(step: int):
    """Best-effort draft save + re-rendered summary panel.

    The wizard sidebar re-renders after every Next, which feels laggy when
    the user is still filling the current step. This endpoint accepts the
    in-progress form data, applies the step-specific persister (wrapped in
    try/except so garbage input can't break navigation), and returns just
    the re-rendered summary panel HTML. The client swaps ``#wizard_summary``
    in place, so the sidebar mirrors what the user is typing.
    """
    params_dict = session.get("params", {}) or {}

    # Step 1's fields are a special case: they map 1:1 onto Params but
    # there is no ``_apply_step1`` (the route builds Params directly).
    if step == 1:
        form = request.form
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
    elif step in _DRAFT_PERSISTERS:
        try:
            _DRAFT_PERSISTERS[step](params_dict, request.form)
        except Exception:
            # Swallow — a half-filled form shouldn't break the summary.
            pass

    session["params"] = params_dict
    return render_template("generator/_summary_partial.html", params=params_dict)
