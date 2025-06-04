from flask import render_template, request, redirect, url_for, session
from app.modules.generator import generator_bp
from fm_generator.src.fm_generator.FMGenerator.models.config import Params
import os
from flask import send_file
import tempfile
import shutil
from datetime import datetime
from fm_generator.src.fm_generator.FMGenerator.models.models import FmgeneratorModel
from app.modules.generator.services import GeneratorService
from flamapy.metamodels.fm_metamodel.models.feature_model import Attribute, Domain, Range  # Ajusta el import si es necesario

generator_service = GeneratorService()

def validate_step1_form(form):
    """Valida los campos del formulario de step1 y devuelve (errores, valores)."""
    errors = {}
    values = {}  # Para rellenar el formulario en caso de error

    num_models_val = form.get('num_models_val', '').strip()
    seed_val = form.get('seed', '').strip()

    # Validar NUM_MODELS
    try:
        num_models = int(num_models_val)
        if not (1 <= num_models <= 10000):
            errors['num_models_val'] = 'Number of models must be between 1 and 10,000.'
    except Exception:
        errors['num_models_val'] = 'Number of models must be an integer.'

    # Validar SEED
    try:
        seed = int(seed_val)
        if seed <= 0:
            errors['seed'] = 'Seed must be a positive integer.'
    except Exception:
        errors['seed'] = 'Seed must be a positive integer.'

    # Guardar valores introducidos para recargar el formulario
    for k in form:
        values[k] = form[k]

    return errors, values



# Paso 1: solo guarda los valores y pasa a step2
@generator_bp.route('/generator/step1', methods=['GET', 'POST'])
def step1():
    if request.method == 'POST':
        errors, values = validate_step1_form(request.form)
        
        # Si hay errores en la validación inicial
        if errors:
            print(f"[VALIDACIÓN STEP1] Errores detectados: {errors}")
            return render_template('generator/step1.html', current_step=1, errors=errors, values=values)
        
        # Si pasa la validación, intentamos construir Params (llama a __post_init__)
        try:
            params = Params(
                NUM_MODELS = int(request.form.get('num_models_val')),
                SEED = int(request.form.get('seed')),
                ENSURE_SATISFIABLE = 'ensure_satisfiable' in request.form,
                NAME_PREFIX = request.form.get('name_prefix', ''),
                INCLUDE_FEATURE_COUNT_SUFFIX = 'feature_count_suffix' in request.form,
                INCLUDE_CONSTRAINT_COUNT_SUFFIX = 'constraint_count_suffix' in request.form,
            )
        except ValueError as e:
            # Error lanzado por __post_init__, lo mostramos en consola y frontend
            print(f"[Params __post_init__ ERROR] {e}")
            errors['global'] = str(e)
            return render_template('generator/step1.html', current_step=1, errors=errors, values=request.form)

        # Sin errores: guardamos en sesión y redirigimos
        session['params'] = params.__dict__
        return redirect(url_for('generator.step2'))

    # GET: valores por defecto
    default_values = {
        'num_models_val': 5,
        'seed': 42,
        'name_prefix': '',
        'ensure_satisfiable': 'on',
        'feature_count_suffix': '',
        'constraint_count_suffix': ''
    }
    return render_template('generator/step1.html', current_step=1, errors={}, values=default_values)



def validate_step2_form(form):
    """
    Valida los campos del formulario de step2 y devuelve (errores, valores).
    Validaciones:
    - MIN_FEATURES y MAX_FEATURES: entre 1 y 10000, y MIN <= MAX.
    - MAX_TREE_DEPTH: entre 1 y MAX_FEATURES.
    - Distribuciones DIST_BOOLEAN, DIST_INTEGER, DIST_REAL, DIST_STRING: entre 0 y 1, suma exactamente 1.
    - PROB_FEATURE_CARDINALITY/attach probability (prob_fc): entre 0.01 y 1.
    - Distribución relaciones (DIST_OPTIONAL, DIST_MANDATORY, DIST_ALTERNATIVE, DIST_OR, DIST_GROUP_CARDINALITY): suma 1.
    - Feature cardinality: min/max entre 1 y 10000, min <= max.
    - GROUP_CARDINALITY_MIN >= 1, GROUP_CARDINALITY_MAX <= MAX_FEATURES
    """
    errors = {}
    values = {}

    # Features
    min_features_val = form.get('num_features_min', '').strip()
    max_features_val = form.get('num_features_max', '').strip()
    try:
        min_features = int(min_features_val)
        if not (1 <= min_features <= 10000):
            errors['num_features_min'] = 'Min. features must be between 1 and 10,000.'
    except Exception:
        errors['num_features_min'] = 'Min. features must be an integer.'
    try:
        max_features = int(max_features_val)
        if not (1 <= max_features <= 10000):
            errors['num_features_max'] = 'Max. features must be between 1 and 10,000.'
    except Exception:
        errors['num_features_max'] = 'Max. features must be an integer.'

    if ('num_features_min' not in errors and 'num_features_max' not in errors
        and min_features > max_features):
        errors['num_features_max'] = 'Max. features must be greater than or equal to Min. features.'

    # MAX_TREE_DEPTH
    max_tree_depth_val = form.get('max_tree_depth', '').strip()
    try:
        max_tree_depth = int(max_tree_depth_val)
        if 'num_features_max' not in errors and not (1 <= max_tree_depth <= max_features):
            errors['max_tree_depth'] = 'Maximum tree depth must be between 1 and the maximum number of features.'
    except Exception:
        errors['max_tree_depth'] = 'Maximum tree depth must be an integer.'

    # Distribuciones de features
    dist_fields = ['dist_boolean', 'dist_integer', 'dist_real', 'dist_string']
    dist_values = []
    for f in dist_fields:
        val = form.get(f, '').strip()
        try:
            v = float(val)
            if not (0.0 <= v <= 1.0):
                errors[f] = 'Value must be between 0 and 1.'
            dist_values.append(v)
        except Exception:
            errors[f] = 'Value must be a decimal between 0 and 1.'
            dist_values.append(0.0)
    total_dist = sum(dist_values)
    if abs(total_dist - 1.0) > 0.001:
        for f in dist_fields:
            if f not in errors:
                errors[f] = 'The sum of all distributions must be exactly 1.0.'
        errors['dist_total'] = f"Current sum: {total_dist:.4f}. The total must be 1.0."

    # Attach probability (prob_fc)
    prob_fc_val = form.get('prob_fc')
    if prob_fc_val is not None:
        try:
            ap = float(prob_fc_val.strip())
            if not (0.01 <= ap <= 1.0):
                errors['attach_probability'] = 'Attach probability must be between 0.01 and 1.'
        except Exception:
            errors['attach_probability'] = 'Attach probability must be a decimal between 0.01 and 1.'

    # Feature cardinality min/max
    min_fc_val = form.get('min_feature_cardinality', '').strip()
    max_fc_val = form.get('max_feature_cardinality', '').strip()
    try:
        min_fc = int(min_fc_val)
        if not (1 <= min_fc <= 10000):
            errors['min_feature_cardinality'] = 'Min. feature cardinality must be between 1 and 10,000.'
    except Exception:
        errors['min_feature_cardinality'] = 'Min. feature cardinality must be an integer.'
    try:
        max_fc = int(max_fc_val)
        if not (1 <= max_fc <= 10000):
            errors['max_feature_cardinality'] = 'Max. feature cardinality must be between 1 and 10,000.'
    except Exception:
        errors['max_feature_cardinality'] = 'Max. feature cardinality must be an integer.'
    if ('min_feature_cardinality' not in errors and 'max_feature_cardinality' not in errors
        and min_fc > max_fc):
        errors['max_feature_cardinality'] = 'Max. feature cardinality must be greater than or equal to min.'

    # Distribución de relaciones (groups)
    rel_fields = ['dist_optional', 'dist_mandatory', 'dist_alternative', 'dist_or', 'dist_group_cardinality']
    rel_values = []
    for f in rel_fields:
        val = form.get(f, '').strip()
        try:
            v = float(val)
            if not (0.0 <= v <= 1.0):
                errors[f] = 'Value must be between 0 and 1.'
            rel_values.append(v)
        except Exception:
            errors[f] = 'Value must be a decimal between 0 and 1.'
            rel_values.append(0.0)
    rel_total = sum(rel_values)
    if abs(rel_total - 1.0) > 0.001:
        for f in rel_fields:
            if f not in errors:
                errors[f] = 'The sum of all relation distributions must be exactly 1.0.'
        errors['rel_dist_total'] = f"Current sum: {rel_total:.4f}. The total must be 1.0."

    # Group cardinality min/max
    group_card_min_val = form.get('group_cardinality_min', '').strip()
    group_card_max_val = form.get('group_cardinality_max', '').strip()
    try:
        group_card_min = int(group_card_min_val)
        if group_card_min < 1:
            errors['group_cardinality_min'] = 'Group cardinality min must be at least 1.'
    except Exception:
        errors['group_cardinality_min'] = 'Group cardinality min must be an integer.'
    try:
        group_card_max = int(group_card_max_val)
        if 'num_features_max' not in errors and group_card_max > max_features:
            errors['group_cardinality_max'] = 'Group cardinality max cannot be greater than the maximum number of features.'
    except Exception:
        errors['group_cardinality_max'] = 'Group cardinality max must be an integer.'
    if ('group_cardinality_min' not in errors and 'group_cardinality_max' not in errors
        and group_card_min > group_card_max):
        errors['group_cardinality_max'] = 'Group cardinality max must be greater than or equal to min.'

    # Guardar valores introducidos
    for k in form:
        values[k] = form[k]
    # Añade los totales para mostrar en el template
    values['dist_total'] = f"{total_dist:.4f}"
    values['rel_dist_total'] = f"{rel_total:.4f}"

    return errors, values




# Paso 2: genera y descarga el zip en POST
@generator_bp.route('/generator/step2', methods=['GET', 'POST'])
def step2():
    if request.method == 'POST':
        errors, values = validate_step2_form(request.form)
        if errors:
            print(f"[VALIDACIÓN STEP2] Errores detectados: {errors}")
            return render_template('generator/step2.html', current_step=2, errors=errors, values=values)

        params_dict = session.get('params')
        if not params_dict:
            return "Error: Params missing in session", 400

        # Niveles de lenguaje
        params_dict['GROUP_CARDINALITY'] = 'group_cardinality' in request.form
        params_dict['ARITHMETIC_LEVEL'] = 'arithmetic_level' in request.form
        params_dict['TYPE_LEVEL'] = 'type_level' in request.form
        params_dict['FEATURE_CARDINALITY'] = 'feature_cardinality' in request.form
        params_dict['AGGREGATE_FUNCTIONS'] = 'aggregate_functions' in request.form
        params_dict['STRING_CONSTRAINTS'] = 'string_constraints' in request.form

        params_dict['MIN_FEATURES'] = int(request.form.get('num_features_min', 1))
        params_dict['MAX_FEATURES'] = int(request.form.get('num_features_max', 10))
        params_dict['DIST_BOOLEAN'] = float(request.form.get('dist_boolean', 0.7))
        params_dict['DIST_INTEGER'] = float(request.form.get('dist_integer', 0.2))
        params_dict['DIST_REAL'] = float(request.form.get('dist_real', 0.0))
        params_dict['DIST_STRING'] = float(request.form.get('dist_string', 0.0))

        # Tree depth
        params_dict['MAX_TREE_DEPTH'] = int(request.form.get('max_tree_depth', 5))

        # Groups
        params_dict['DIST_OPTIONAL'] = float(request.form.get('dist_optional', 0.7))
        params_dict['DIST_MANDATORY'] = float(request.form.get('dist_mandatory', 0.2))
        params_dict['DIST_ALTERNATIVE'] = float(request.form.get('dist_alternative', 0.0))
        params_dict['DIST_OR'] = float(request.form.get('dist_or', 0.0))

        # Group cardinality
        params_dict['DIST_GROUP_CARDINALITY'] = float(request.form.get('dist_group_cardinality', 0.1))
        params_dict['GROUP_CARDINALITY_MIN'] = int(request.form.get('group_cardinality_min', 1))
        params_dict['GROUP_CARDINALITY_MAX'] = int(request.form.get('group_cardinality_max', 10))

        # Feature cardinality y attach_prob
        params_dict['PROB_FEATURE_CARDINALITY'] = float(request.form.get('prob_fc', 0.05))
        params_dict['MIN_FEATURE_CARDINALITY'] = int(request.form.get('min_feature_cardinality', 2))
        params_dict['MAX_FEATURE_CARDINALITY'] = int(request.form.get('max_feature_cardinality', 5))

        # Checkbox (nivel de lenguaje) – Boolean, Arithmetic, etc (si algún día habilitas)
        params_dict['GROUP_CARDINALITY'] = 'group_cardinality' in request.form

        # Actualiza el objeto Params
        params = Params(**params_dict)
        session['params'] = params.__dict__

        print(params)

        return redirect(url_for('generator.step3'))

    current_step = 2
    default_values = {
        'num_features_min': 10,
        'num_features_max': 50,
        'dist_boolean': 0.7,
        'dist_integer': 0.1,
        'dist_real': 0.1,
        'dist_string': 0.1,
        'prob_fc': 0.1,
        'min_feature_cardinality': 2,
        'max_feature_cardinality': 5,
        'max_tree_depth': 5,
        'dist_optional': 0.3,
        'dist_mandatory': 0.3,
        'dist_alternative': 0.2,
        'dist_or': 0.2,
        'dist_group_cardinality': 0.0,
        'group_cardinality_min': 10,
        'group_cardinality_max': 50,
        'dist_total': "1.0000",
        'rel_dist_total': "1.0000"
    }
    return render_template('generator/step2.html', current_step=current_step, errors={}, values=default_values)



def validate_step3_form(form, max_features):
    """
    Valida los campos del formulario de step3 y devuelve (errores, valores).
    Validaciones:
    - MIN_CONSTRAINTS >= 1
    - MAX_CONSTRAINTS <= 10000 y >= MIN_CONSTRAINTS
    - MAX_VARS_PER_CONSTRAINT <= MAX_FEATURES y >= MIN_VARS_PER_CONSTRAINT
    - EXTRA_CONSTRAINT_REPRESENTATIVENESS < MAX_VARS_PER_CONSTRAINT
    """
    errors = {}
    values = {}

    # Número de constraints
    min_constraints_val = form.get('num_constraints_min', '').strip()
    max_constraints_val = form.get('num_constraints_max', '').strip()
    try:
        min_constraints = int(min_constraints_val)
        if min_constraints < 1:
            errors['num_constraints_min'] = 'Min. constraints must be at least 1.'
    except Exception:
        errors['num_constraints_min'] = 'Min. constraints must be an integer.'

    try:
        max_constraints = int(max_constraints_val)
        if max_constraints > 10000:
            errors['num_constraints_max'] = 'Max. constraints cannot exceed 10,000.'
    except Exception:
        errors['num_constraints_max'] = 'Max. constraints must be an integer.'

    if ('num_constraints_min' not in errors and 'num_constraints_max' not in errors
        and min_constraints > max_constraints):
        errors['num_constraints_max'] = 'Max. constraints must be greater than or equal to min.'

    # Variables por constraint
    min_vars_val = form.get('vars_per_ctc_min', '').strip()
    max_vars_val = form.get('vars_per_ctc_max', '').strip()
    try:
        min_vars = int(min_vars_val)
        if min_vars < 1:
            errors['vars_per_ctc_min'] = 'Min. variables per constraint must be at least 1.'
    except Exception:
        errors['vars_per_ctc_min'] = 'Min. variables per constraint must be an integer.'

    try:
        max_vars = int(max_vars_val)
        if max_vars > max_features:
            errors['vars_per_ctc_max'] = f'Max. variables per constraint cannot exceed max features ({max_features}).'
    except Exception:
        errors['vars_per_ctc_max'] = 'Max. variables per constraint must be an integer.'

    if ('vars_per_ctc_min' not in errors and 'vars_per_ctc_max' not in errors
        and min_vars > max_vars):
        errors['vars_per_ctc_max'] = 'Max. variables per constraint must be greater than or equal to min.'

    # Extra Constraint Representativeness
    extra_repr_val = form.get('extra_constraint_repr', '').strip()
    try:
        extra_repr = int(extra_repr_val)
        if 'vars_per_ctc_max' not in errors and extra_repr >= max_vars:
            errors['extra_constraint_repr'] = 'Extra constraint representativeness must be less than max. variables per constraint.'
        if extra_repr < 1:
            errors['extra_constraint_repr'] = 'Extra constraint representativeness must be at least 1.'
    except Exception:
        errors['extra_constraint_repr'] = 'Extra constraint representativeness must be an integer.'

    # Guarda valores introducidos
    for k in form:
        values[k] = form[k]

    return errors, values




@generator_bp.route('/generator/step3', methods=['GET', 'POST'])
def step3():
    # Para las validaciones dependientes de max_features:
    params_dict = session.get('params')
    if params_dict:
        max_features = params_dict.get('MAX_FEATURES', 10000)
    else:
        max_features = 10000

    if request.method == 'POST':
        errors, values = validate_step3_form(request.form, max_features)
        if errors:
            print(f"[VALIDACIÓN STEP3] Errores detectados: {errors}")
            return render_template('generator/step3.html', current_step=3, errors=errors, values=values)

        if not params_dict:
            return "Error: Params missing in session", 400

        # Recoge todos los parámetros de constraints
        params_dict['MIN_CONSTRAINTS'] = int(request.form.get('num_constraints_min', 0))
        params_dict['MAX_CONSTRAINTS'] = int(request.form.get('num_constraints_max', 0))
        params_dict['EXTRA_CONSTRAINT_REPRESENTATIVENESS'] = int(request.form.get('extra_constraint_repr', 1))

        params_dict['MIN_VARS_PER_CONSTRAINT'] = int(request.form.get('vars_per_ctc_min', 1))
        params_dict['MAX_VARS_PER_CONSTRAINT'] = int(request.form.get('vars_per_ctc_max', 10))

        params_dict['CTC_DIST_BOOLEAN'] = float(request.form.get('ctc_dist_boolean', 0.7))
        params_dict['CTC_DIST_INTEGER'] = float(request.form.get('ctc_dist_integer', 0.2))
        params_dict['CTC_DIST_REAL'] = float(request.form.get('ctc_dist_real', 0.7))
        params_dict['CTC_DIST_STRING'] = float(request.form.get('ctc_dist_string', 0.0))

        # Boolean level
        params_dict['PROB_NOT'] = float(request.form.get('prob_not', 0.3))
        params_dict['PROB_AND'] = float(request.form.get('prob_and', 0.7))
        params_dict['PROB_OR_CT'] = float(request.form.get('prob_or', 0.1))
        params_dict['PROB_IMPLICATION'] = float(request.form.get('prob_implies', 0.1))
        params_dict['PROB_EQUIVALENCE'] = float(request.form.get('prob_equiv', 0.1))

        # Arithmetic level
        params_dict['PROB_SUM'] = float(request.form.get('prob_plus', 0.7))
        params_dict['PROB_SUBSTRACT'] = float(request.form.get('prob_minus', 0.2))
        params_dict['PROB_MULTIPLY'] = float(request.form.get('prob_times', 0.7))
        params_dict['PROB_DIVIDE'] = float(request.form.get('prob_div', 0.0))
        params_dict['PROB_EQUALS'] = float(request.form.get('prob_eq', 0.0))
        params_dict['PROB_LESS'] = float(request.form.get('prob_lt', 0.2))
        params_dict['PROB_GREATER'] = float(request.form.get('prob_gt', 0.7))
        params_dict['PROB_LESS_EQUALS'] = float(request.form.get('prob_leq', 0.0))
        params_dict['PROB_GREATER_EQUALS'] = float(request.form.get('prob_geq', 0.0))

        # Aggregate functions
        params_dict['PROB_SUM_FUNCTION'] = float(request.form.get('prob_sum', 0.0))
        params_dict['PROB_AVG_FUNCTION'] = float(request.form.get('prob_avg', 0.0))

        # Type level
        params_dict['PROB_LEN_FUNCTION'] = float(request.form.get('prob_len', 0.7))

        # Actualiza el objeto Params
        params = Params(**params_dict)
        session['params'] = params.__dict__

        print(params)

        return redirect(url_for('generator.step4'))

    current_step = 3
    # Puedes usar los valores por defecto o los que quieras
    default_values = {
        'num_constraints_min': 1,
        'num_constraints_max': 10,
        'extra_constraint_repr': 1,
        'vars_per_ctc_min': 1,
        'vars_per_ctc_max': 10,
        # ... y el resto por defecto si quieres pasárselos al render
    }
    return render_template('generator/step3.html', current_step=current_step, errors={}, values=default_values)



@generator_bp.route('/generator/step4', methods=['GET', 'POST'])
def step4():
    if request.method == 'POST':
        params_dict = session.get('params')
        if not params_dict:
            return "Error: Params missing in session", 400

        random_attributes = 'random_attributes' in request.form
        params_dict['RANDOM_ATTRIBUTES'] = random_attributes

        if random_attributes:
            params_dict['MIN_ATTRIBUTES'] = int(request.form.get('min_attributes', 1))
            params_dict['MAX_ATTRIBUTES'] = int(request.form.get('max_attributes', 5))
            # Guarda listas vacías (datos nativos)
            params_dict['ATTRIBUTES_LIST'] = []
            params_dict['ATTRIBUTE_ATTACH_PROBS'] = []
            params_dict['ATTRIBUTE_IN_CONSTRAINTS'] = []
        else:
            attr_names = request.form.getlist('attr_name')
            attr_types = request.form.getlist('attr_type')
            attr_defaults = request.form.getlist('attr_value')
            attr_attach_probs = request.form.getlist('attr_attach_prob')
            attr_use_in_constraints = request.form.getlist('attr_use_in_constraints')

            attributes_data = []
            attach_probs_list = []
            in_constraints_list = []

            # Formatea 'use_in_constraints' como set de índices (checkbox)
            constraints_checked = set()
            if attr_use_in_constraints:
                # Si hay uno solo, puede llegar como string; si varios, como lista
                if isinstance(attr_use_in_constraints, list):
                    for idx, v in enumerate(attr_use_in_constraints):
                        if v == 'on' or v == str(idx):
                            constraints_checked.add(idx)
                else:
                    if attr_use_in_constraints == 'on':
                        constraints_checked.add(0)

            for i in range(len(attr_names)):
                name = attr_names[i]
                type_ = attr_types[i].lower()
                default_value = attr_defaults[i]

                # Guarda solo como dict serializable (NO como instancia de Attribute)
                attr_dict = {
                    'name': name,
                    'type': type_,
                    'default_value': default_value,
                }
                attributes_data.append(attr_dict)
                attach_probs_list.append(float(attr_attach_probs[i]) if attr_attach_probs[i] else 1.0)
                in_constraints_list.append(i in constraints_checked)

            params_dict['MIN_ATTRIBUTES'] = None
            params_dict['MAX_ATTRIBUTES'] = None
            params_dict['ATTRIBUTES_LIST'] = attributes_data
            params_dict['ATTRIBUTE_ATTACH_PROBS'] = attach_probs_list
            params_dict['ATTRIBUTE_IN_CONSTRAINTS'] = in_constraints_list

        # GUARDA SOLO DATOS PRIMITIVOS EN SESSION
        session['params'] = params_dict

        print(params_dict)

        # === Justo antes de generar modelos: construye los objetos Attribute si hace falta ===
        # (Nunca los metas en la sesión!)
        # --- Carga de params y conversión de atributos ---
        params = Params(**params_dict)

        # Si es manual, construye la lista de Attribute:
        if not params.RANDOM_ATTRIBUTES and params.ATTRIBUTES_LIST:
            rebuilt_attrs = []
            for attr in params.ATTRIBUTES_LIST:
                type_ = attr['type']
                name = attr['name']
                value = attr['default_value']

                if type_ == 'boolean':
                    domain = Domain(ranges=None, elements=[True, False])
                    default_value = True if value == "True" else False
                elif type_ == 'integer':
                    domain = Domain(ranges=[Range(0, 100)], elements=None)
                    default_value = int(value) if value else 0
                elif type_ == 'real':
                    domain = Domain(ranges=[Range(0, 100)], elements=None)
                    default_value = float(value) if value else 0.0
                elif type_ == 'string':
                    domain = Domain(ranges=None, elements=None)
                    default_value = value or ""
                else:
                    domain = Domain(ranges=None, elements=None)
                    default_value = value

                rebuilt_attrs.append(
                    Attribute(name=name, domain=domain, default_value=default_value)
                )
            params.ATTRIBUTES_LIST = rebuilt_attrs

        return redirect(url_for('generator.step5'))

    current_step = 4
    return render_template('generator/step4.html', current_step=current_step)


@generator_bp.route('/generator/step5', methods=['GET'])
def step5():
    current_step = 5
    return render_template('generator/step5.html', current_step=current_step)

# Endpoint dedicado SOLO para descarga
@generator_bp.route('/generator/download', methods=['GET'])
def download_models():
    params_dict = session.get('params')
    if not params_dict:
        return "Error: Params missing in session", 400

    # Reconstruye el objeto Params (y lista de Attribute si toca, como en step4)
    params = Params(**params_dict)

    # Reconstruimos ATTRIBUTES_LIST
    if not params.RANDOM_ATTRIBUTES and params.ATTRIBUTES_LIST:
        rebuilt_attrs = []
        for attr in params.ATTRIBUTES_LIST:
            type_ = attr['type']
            name = attr['name']
            value = attr['default_value']

            if type_ == 'boolean':
                domain = Domain(ranges=None, elements=[True, False])
                default_value = True if value == "True" else False
            elif type_ == 'integer':
                domain = Domain(ranges=[Range(0, 100)], elements=None)
                default_value = int(value) if value else 0
            elif type_ == 'real':
                domain = Domain(ranges=[Range(0, 100)], elements=None)
                default_value = float(value) if value else 0.0
            elif type_ == 'string':
                domain = Domain(ranges=None, elements=None)
                default_value = value or ""
            else:
                domain = Domain(ranges=None, elements=None)
                default_value = value

            rebuilt_attrs.append(
                Attribute(name=name, domain=domain, default_value=default_value)
            )
        params.ATTRIBUTES_LIST = rebuilt_attrs

    # Genera los modelos y el zip SOLO aquí
    temp_dir = tempfile.mkdtemp()
    output_dir = os.path.join(temp_dir, "models_output")
    os.makedirs(output_dir, exist_ok=True)
    fm_generator = FmgeneratorModel(params)
    fm_generator.generate_models(output_dir)
    zip_path = os.path.join(temp_dir, "feature_models.zip")
    generator_service.zip_generated_models(output_dir, zip_path)
    zip_filename = f"fms.zip"
    try:
        return send_file(zip_path, as_attachment=True, download_name=zip_filename)
    finally:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
