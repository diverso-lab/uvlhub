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
from app.modules.generator.validators import (
    validate_step1_form,
    validate_step2_form,
    validate_step3_form,
    validate_step4_form,
    validate_step5_form,
)
from app.modules.generator.wizard_state import (
    clear_step_state,
    save_step_state,
    update_summary_draft,
)

from app.modules.generator.wizard_persisters import (
    add_level_flags,
    apply_step1_batch,
    apply_step2_levels,
    apply_step3_tree,
    apply_step4_constraints,
    apply_step5_attributes,
    apply_step6_output,
)

from app.modules.generator.wizard_builders import (
    build_step1_values,
    build_step2_values,
    build_step3_values,
    build_step4_values,
    build_step5_values,
    build_step6_values,
)
from app.modules.generator.constants import (
    STEP2_CHECKBOX_FIELDS,
    STEP5_CHECKBOX_FIELDS,
    STEP6_CHECKBOX_FIELDS,
)


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
            apply_step1_batch(p, request.form)
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

    values = build_step1_values(session.get("params", {}))
    return render_template("generator/step1.html", current_step=1, errors={}, values=values)


# ─── Step 2 · Language levels ────────────────────────────────────────────


@generator_bp.route("/generator/random/step2", methods=["GET", "POST"])
def step2():
    if request.method == "POST":
        nav = request.form.get("nav", "next")
        save_step_state(
            2,
            request.form,
            checkbox_fields=STEP2_CHECKBOX_FIELDS
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

    values = build_step2_values(session.get("params", {}))
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
        add_level_flags(values, params_dict)
        if errors:
            return render_template("generator/step3.html", current_step=3, errors=errors, values=values)
        apply_step3_tree(params_dict, request.form)
        session["params"] = params_dict
        clear_step_state(3)
        return redirect(url_for("generator.step4"))

    values = build_step3_values(params_dict)
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
        add_level_flags(values, params_dict)
        if errors:
            return render_template("generator/step4.html", current_step=4, errors=errors, values=values)
        apply_step4_constraints(params_dict, request.form)
        session["params"] = params_dict
        clear_step_state(4)
        return redirect(url_for("generator.step5"))

    values = build_step4_values(params_dict)
    return render_template("generator/step4.html", current_step=4, errors={}, values=values)


# ─── Step 5 · Attributes ─────────────────────────────────────────────────


@generator_bp.route("/generator/random/step5", methods=["GET", "POST"])
def step5():
    params_dict = session.get("params")
    if not params_dict:
        return redirect(url_for("generator.landing"))

    if request.method == "POST":
        nav = request.form.get("nav", "next")
        save_step_state(5, request.form, checkbox_fields=STEP5_CHECKBOX_FIELDS)

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

    values = build_step5_values(params_dict)
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
            checkbox_fields=STEP6_CHECKBOX_FIELDS
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

    values = build_step6_values(params_dict)
    return render_template("generator/step6.html", current_step=6, errors={}, values=values)


# ─── Pyodide endpoint ────────────────────────────────────────────────────


@generator_bp.route("/generator/random/params-json", methods=["GET"])
def get_params_json():
    params = session.get("params")
    if not params:
        return jsonify({"error": "Params missing"}), 400
    return jsonify(params)



@generator_bp.route("/generator/random/summary-refresh/<int:step>", methods=["POST"])
def refresh_summary(step: int):
    params_dict = update_summary_draft(step, request.form)
    return render_template("generator/_summary_partial.html", params=params_dict)