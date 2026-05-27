from app.modules.generator.wizard_persisters import safe_float


def validate_step1_form(form):
    """Step 1 — batch. num_models + seed + name_prefix."""
    errors, values = {}, {}

    num_models_val = form.get("num_models_val", "").strip()
    try:
        num_models = int(num_models_val)
        if num_models < 1:
            errors["num_models_val"] = "Number of models must be at least 1."
        elif num_models > 1000:
            errors["num_models_val"] = "Number of models cannot exceed 1000."
    except Exception:
        errors["num_models_val"] = "Number of models must be an integer."

    seed_val = form.get("seed", "").strip()
    try:
        seed = int(seed_val)
        if seed <= 0:
            errors["seed"] = "Seed must be a positive integer."
    except Exception:
        errors["seed"] = "Seed must be a positive integer."

    for k in form:
        values[k] = form[k]
    return errors, values


def validate_step2_form(form):
    """Step 2 — language levels. All checkboxes; nothing to numerically
    validate. We simply enforce that minor levels are only on if their
    major is on (the engine does this too, but failing fast here keeps
    the UI honest)."""
    errors, values = {}, {}
    arith = "arithmetic_level" in form
    type_ = "type_level" in form
    feat_card = "feature_cardinality" in form
    aggregate = "aggregate_functions" in form
    string_ctc = "string_constraints" in form
    group_card = "group_cardinality" in form

    if feat_card and not arith:
        errors["feature_cardinality"] = "Requires Arithmetic level."
    if aggregate and not arith:
        errors["aggregate_functions"] = "Requires Arithmetic level."
    if string_ctc and not type_:
        errors["string_constraints"] = "Requires Type level."

    values.update(
        {
            "arithmetic_level": arith,
            "type_level": type_,
            "feature_cardinality": feat_card,
            "aggregate_functions": aggregate,
            "string_constraints": string_ctc,
            "group_cardinality": group_card,
        }
    )
    return errors, values


def validate_step3_form(form, params_dict=None):
    """Step 3 — feature tree. min/max features, depth, rel dist, and the
    feat/group cardinality blocks.

    `params_dict` carries the level flags decided in step 2. If omitted,
    we fall back to reading a hidden input from the form."""
    params_dict = params_dict or {}
    errors, values = {}, {}

    # Features
    try:
        min_features = int(form.get("num_features_min", "").strip())
        if min_features < 1:
            errors["num_features_min"] = "Min. features must be at least 1."
    except Exception:
        min_features = None
        errors["num_features_min"] = "Min. features must be an integer."

    try:
        max_features = int(form.get("num_features_max", "").strip())
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
        errors["num_features_max"] = "Max. features must be ≥ Min. features."

    # Tree depth
    try:
        max_tree_depth = int(form.get("max_tree_depth", "").strip())
        if "num_features_max" not in errors and not (1 <= max_tree_depth <= max_features):
            errors["max_tree_depth"] = "Maximum tree depth must be between 1 and Max. features."
    except Exception:
        errors["max_tree_depth"] = "Maximum tree depth must be an integer."

    # Relation distribution (including group cardinality if its toggle is on)
    group_cardinality_enabled = bool(
        params_dict.get("GROUP_CARDINALITY") if "GROUP_CARDINALITY" in params_dict else "group_cardinality" in form
    )
    feature_cardinality_enabled = bool(
        params_dict.get("FEATURE_CARDINALITY")
        if "FEATURE_CARDINALITY" in params_dict
        else "feature_cardinality" in form
    )
    rel_fields = ["dist_optional", "dist_mandatory", "dist_alternative", "dist_or"]
    if group_cardinality_enabled:
        rel_fields.append("dist_group_cardinality")
    rel_values = []
    for f in rel_fields:
        try:
            v = safe_float(form.get(f, "").strip(), 0.0)
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
                errors[f] = "The relation-distribution probabilities must sum to 1.0."
        errors["rel_dist_total"] = f"Current sum: {rel_total:.4f}. Must be 1.0."
    values["rel_dist_total"] = f"{rel_total:.4f}"

    # Group cardinality min/max (only when the toggle is on)
    if group_cardinality_enabled:
        try:
            gc_min = int(form.get("group_cardinality_min", "").strip())
            if gc_min < 1:
                errors["group_cardinality_min"] = "Group cardinality min must be at least 1."
        except Exception:
            gc_min = None
            errors["group_cardinality_min"] = "Group cardinality min must be an integer."
        try:
            gc_max = int(form.get("group_cardinality_max", "").strip())
            if "num_features_max" not in errors and max_features and gc_max > max_features:
                errors["group_cardinality_max"] = "Group cardinality max cannot exceed Max. features."
            elif gc_max < 1:
                errors["group_cardinality_max"] = "Group cardinality max must be at least 1."
        except Exception:
            gc_max = None
            errors["group_cardinality_max"] = "Group cardinality max must be an integer."
        if (
            "group_cardinality_min" not in errors
            and "group_cardinality_max" not in errors
            and gc_min is not None
            and gc_max is not None
            and gc_min > gc_max
        ):
            errors["group_cardinality_max"] = "Group cardinality max must be ≥ min."

    # Feature cardinality block (only when the toggle is on in step 2)
    if feature_cardinality_enabled:
        prob_fc_val = form.get("prob_fc")
        if prob_fc_val is not None:
            try:
                ap = safe_float(prob_fc_val, 0.0)
                if not (0.0 <= ap <= 1.0):
                    errors["prob_fc"] = "Attach probability must be between 0 and 1."
            except Exception:
                errors["prob_fc"] = "Attach probability must be a number between 0 and 1."

    for k in form:
        values[k] = form[k]
    return errors, values


def validate_step4_form(form, max_features: int = 10000, params_dict=None):
    """Step 4 — constraints. Number / vars ranges + all probability
    distributions.

    `params_dict` carries the level flags decided in step 2 (ARITHMETIC_LEVEL,
    TYPE_LEVEL, etc.). If omitted, we fall back to the form (which may also
    carry hidden mirror inputs)."""
    params_dict = params_dict or {}
    errors, values = {}, {}

    # 1) Number of constraints
    try:
        min_constraints = int(form.get("num_constraints_min", "").strip())
        if min_constraints < 1:
            errors["num_constraints_min"] = "Min. constraints must be at least 1."
    except Exception:
        min_constraints = None
        errors["num_constraints_min"] = "Min. constraints must be an integer."
    try:
        max_constraints = int(form.get("num_constraints_max", "").strip())
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
        errors["num_constraints_max"] = "Max. constraints must be ≥ Min. constraints."

    # 2) Extra constraint representativeness
    try:
        extra_cr = int(form.get("extra_constraint_repr", "").strip())
    except Exception:
        extra_cr = None
        errors["extra_constraint_repr"] = "Must be an integer."

    # 3) Vars per constraint
    try:
        vpc_max = int(form.get("vars_per_ctc_max", "").strip())
        if vpc_max < 1:
            errors["vars_per_ctc_max"] = "Max. vars per constraint must be at least 1."
    except Exception:
        vpc_max = None
        errors["vars_per_ctc_max"] = "Max. vars per constraint must be an integer."

    if extra_cr is not None and vpc_max is not None:
        if extra_cr < 1:
            errors["extra_constraint_repr"] = "Must be ≥ 1."
        elif extra_cr > vpc_max:
            errors["extra_constraint_repr"] = "Must be ≤ Max. vars per constraint."

    try:
        vpc_min = int(form.get("vars_per_ctc_min", "").strip())
        if vpc_min < 1:
            errors["vars_per_ctc_min"] = "Min. vars per constraint must be at least 1."
    except Exception:
        vpc_min = None
        errors["vars_per_ctc_min"] = "Min. vars per constraint must be an integer."

    if isinstance(vpc_max, int) and vpc_max > max_features:
        errors["vars_per_ctc_max"] = "Max. vars per constraint cannot exceed Max. features."

    if (
        "vars_per_ctc_min" not in errors
        and "vars_per_ctc_max" not in errors
        and vpc_min is not None
        and isinstance(vpc_max, int)
        and vpc_min > vpc_max
    ):
        errors["vars_per_ctc_max"] = "Max. vars per constraint must be ≥ Min."

    # 4) Boolean operators (+ NOT)
    prob_not = safe_float(form.get("prob_not"), 0.0)
    if not (0.0 <= prob_not <= 1.0):
        errors["prob_not"] = "Value must be between 0 and 1."
    prob_and = safe_float(form.get("prob_and"), 0.0)
    prob_or = safe_float(form.get("prob_or"), 0.0)
    prob_implies = safe_float(form.get("prob_implies"), 0.0)
    prob_equiv = safe_float(form.get("prob_equiv"), 0.0)
    sum_bool = prob_and + prob_or + prob_implies + prob_equiv
    if abs(sum_bool - 1.0) > 0.001:
        for f in ("prob_and", "prob_or", "prob_implies", "prob_equiv"):
            if f not in errors:
                errors[f] = "The boolean-connective probabilities must sum to 1.0."
        errors["boolop_sum"] = f"Current sum: {sum_bool:.4f}. Must be 1.0."
    values["boolop_sum"] = f"{sum_bool:.4f}"

    # 5) Arithmetic (conditional) + comparison (conditional).
    # Prefer params_dict (step 2 truth) over any form mirrors.
    arith_on = (
        params_dict.get("ARITHMETIC_LEVEL")
        if "ARITHMETIC_LEVEL" in params_dict
        else form.get("arithmetic_level") in ("on", "true", "1", True)
    )
    agg_on = (
        params_dict.get("AGGREGATE_FUNCTIONS")
        if "AGGREGATE_FUNCTIONS" in params_dict
        else form.get("aggregate_functions") in ("on", "true", "1", True)
    )
    if arith_on:
        prob_plus = safe_float(form.get("prob_plus"), 0.0)
        prob_minus = safe_float(form.get("prob_minus"), 0.0)
        prob_times = safe_float(form.get("prob_times"), 0.0)
        prob_div = safe_float(form.get("prob_div"), 0.0)
        arith_sum = prob_plus + prob_minus + prob_times + prob_div
        fields = ["prob_plus", "prob_minus", "prob_times", "prob_div"]
        if agg_on:
            prob_sum = safe_float(form.get("prob_sum"), 0.0)
            prob_avg = safe_float(form.get("prob_avg"), 0.0)
            arith_sum += prob_sum + prob_avg
            fields += ["prob_sum", "prob_avg"]
        if abs(arith_sum - 1.0) > 0.001:
            for f in fields:
                if f not in errors:
                    errors[f] = "Arithmetic-level probabilities{} must sum to 1.0.".format(
                        " (including aggregates)" if agg_on else ""
                    )
            errors["arithmetic_sum"] = f"Current sum: {arith_sum:.4f}. Must be 1.0."
        values["arithmetic_sum"] = f"{arith_sum:.4f}"

        prob_eq = safe_float(form.get("prob_eq"), 0.0)
        prob_lt = safe_float(form.get("prob_lt"), 0.0)
        prob_gt = safe_float(form.get("prob_gt"), 0.0)
        prob_leq = safe_float(form.get("prob_leq"), 0.0)
        prob_geq = safe_float(form.get("prob_geq"), 0.0)
        cmp_sum = prob_eq + prob_lt + prob_gt + prob_leq + prob_geq
        if abs(cmp_sum - 1.0) > 0.001:
            for f in ("prob_eq", "prob_lt", "prob_gt", "prob_leq", "prob_geq"):
                if f not in errors:
                    errors[f] = "Comparison-operator probabilities must sum to 1.0."
            errors["cmp_sum"] = f"Current sum: {cmp_sum:.4f}. Must be 1.0."
        values["cmp_sum"] = f"{cmp_sum:.4f}"
    else:
        values["arithmetic_sum"] = "1.0000"
        values["cmp_sum"] = "1.0000"

    # 6) Type level / string constraints — also from step 2.
    type_on = (
        params_dict.get("TYPE_LEVEL")
        if "TYPE_LEVEL" in params_dict
        else form.get("type_level") in ("on", "true", "1", True)
    )
    str_on = (
        params_dict.get("STRING_CONSTRAINTS")
        if "STRING_CONSTRAINTS" in params_dict
        else form.get("string_constraints") in ("on", "true", "1", True)
    )
    if str_on and type_on:
        prob_len = safe_float(form.get("prob_len"), 0.0)
        if not (0.0 <= prob_len <= 1.0):
            errors["prob_len"] = "Value must be between 0 and 1."

    # 7) CTC type distribution (CTC_DIST_*)
    if arith_on or type_on:
        ctc_fields = [
            ("ctc_dist_boolean", True),
            ("ctc_dist_integer", arith_on),
            ("ctc_dist_real", arith_on),
            ("ctc_dist_string", type_on and str_on),
        ]
        active = 0.0
        for field, is_active in ctc_fields:
            v = safe_float(form.get(field), 0.0)
            if not is_active:
                v = 0.0
            if not (0.0 <= v <= 1.0):
                errors[field] = "Value must be between 0 and 1."
            values[field] = v
            if is_active:
                active += v
        if abs(active - 1.0) > 0.001:
            errors["ctc_dist_sum"] = f"Current sum: {active:.4f}. Active type probabilities must total 1.0."
        values["ctc_dist_sum"] = f"{active:.4f}"

    for k in form:
        values[k] = form[k]
    return errors, values


def validate_step5_form(form, params_dict=None):
    """Step 5 — attributes. Mirror of the legacy step4 validator."""
    errors, values = {}, {}
    params_dict = params_dict or {}

    arith_on = bool(params_dict.get("ARITHMETIC_LEVEL", False))
    type_on = bool(params_dict.get("TYPE_LEVEL", False))
    str_on = bool(params_dict.get("STRING_CONSTRAINTS", False))

    random_checked = "random_attributes" in form
    values["random_attributes"] = random_checked

    if random_checked:
        try:
            min_attr = int(form.get("min_attributes", "").strip())
            if not (1 <= min_attr <= 1000):
                errors["min_attributes"] = "Min. attributes must be between 1 and 1000."
        except Exception:
            min_attr = None
            errors["min_attributes"] = "Min. attributes must be an integer."
        try:
            max_attr = int(form.get("max_attributes", "").strip())
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
            errors["max_attributes"] = "Max. attributes must be ≥ Min."
        values["min_attributes"] = form.get("min_attributes", "")
        values["max_attributes"] = form.get("max_attributes", "")

        # Attribute-type distribution
        dist_fields = [
            ("dist_boolean", True),
            ("dist_integer", arith_on),
            ("dist_real", arith_on),
            ("dist_string", type_on),
        ]
        active_total = 0.0
        for field, is_active in dist_fields:
            v = safe_float(form.get(field), 0.0)
            if not is_active:
                v = 0.0
            if not (0.0 <= v <= 1.0):
                errors[field] = "Value must be between 0 and 1."
            values[field] = v
            if is_active:
                active_total += v
        if abs(active_total - 1.0) > 0.001:
            errors["attr_dist_sum"] = f"Current sum: {active_total:.4f}. Active type probabilities must total 1.0."
        values["attr_dist_sum"] = f"{active_total:.4f}"
    else:
        values["min_attributes"] = ""
        values["max_attributes"] = ""
        # Manual cards — shape-validate each
        attr_count = 0
        while f"attr_name_{attr_count}" in form:
            attr_count += 1
        for i in range(attr_count):
            name = (form.get(f"attr_name_{i}", "") or "").strip()
            if not name:
                errors[f"attr_name_{i}"] = "Attribute name is required."
            type_lc = (form.get(f"attr_type_{i}", "") or "").strip().lower()
            use_in_ctc = form.get(f"attr_use_in_constraints_{i}") == "on"
            if use_in_ctc:
                if type_lc in ("integer", "real") and not arith_on:
                    errors[f"attr_use_in_constraints_{i}"] = (
                        "Integer/Real attrs can be used in constraints only when Arithmetic level is on."
                    )
                elif type_lc == "string" and not (type_on and str_on):
                    errors[f"attr_use_in_constraints_{i}"] = (
                        "String attrs can be used in constraints only when Type level + String constraints are on."
                    )
            prob = (form.get(f"attr_attach_prob_{i}", "") or "").strip()
            if not prob:
                errors[f"attr_attach_prob_{i}"] = "Attach probability is required."
            else:
                try:
                    p = float(prob)
                    if not (0.0 <= p <= 1.0):
                        errors[f"attr_attach_prob_{i}"] = "Attach probability must be between 0 and 1."
                except Exception:
                    errors[f"attr_attach_prob_{i}"] = "Attach probability must be a number."
            if type_lc == "boolean":
                t_checked = form.get(f"attr_value_true_{i}") is not None
                f_checked = form.get(f"attr_value_false_{i}") is not None
                if not (t_checked or f_checked):
                    errors[f"attr_value_bool_{i}"] = "Select at least one boolean value."
            elif type_lc in ("integer", "real", "string"):
                mn = (form.get(f"attr_min_value_{i}", "") or "").strip()
                mx = (form.get(f"attr_max_value_{i}", "") or "").strip()
                if not mn or not mx:
                    errors[f"attr_minmax_{i}"] = "Min and Max are required."
                else:
                    try:
                        if type_lc == "real":
                            lo, hi = float(mn), float(mx)
                        else:
                            lo, hi = int(mn), int(mx)
                        if type_lc == "string" and (lo < 0 or hi < 0):
                            errors[f"attr_minmax_{i}"] = "Min and Max must be non-negative."
                        elif lo > hi:
                            errors[f"attr_minmax_{i}"] = "Min cannot be greater than Max."
                    except Exception:
                        errors[f"attr_minmax_{i}"] = "Min and Max must be numbers."
        for k in form:
            values[k] = form[k]
    return errors, values


def validate_step6_form(form):
    """Step 6 — output options. Just checkboxes; nothing to fail on."""
    return {}, {
        "ensure_satisfiable": "ensure_satisfiable" in form,
        "feature_count_suffix": "feature_count_suffix" in form,
        "constraint_count_suffix": "constraint_count_suffix" in form,
    }