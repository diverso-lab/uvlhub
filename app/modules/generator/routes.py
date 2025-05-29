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

# Paso 1: solo guarda los valores y pasa a step2
@generator_bp.route('/generator/step1', methods=['GET', 'POST'])
def step1():
    if request.method == 'POST':
        params = Params(
            NUM_MODELS = int(request.form.get('num_models_val', 0)),
            SEED = int(request.form.get('seed', 42)),
            ENSURE_SATISFIABLE = 'ensure_satisfiable' in request.form,
            NAME_PREFIX = request.form.get('name_prefix', ''),
            INCLUDE_FEATURE_COUNT_SUFFIX = 'feature_count_suffix' in request.form,
            INCLUDE_CONSTRAINT_COUNT_SUFFIX = 'constraint_count_suffix' in request.form,
        )
        # Guardar como dict
        session['params'] = params.__dict__
        return redirect(url_for('generator.step2'))

    current_step = 1
    return render_template('generator/step1.html', current_step=current_step)

# Paso 2: genera y descarga el zip en POST
@generator_bp.route('/generator/step2', methods=['GET', 'POST'])
def step2():
    if request.method == 'POST':
        params_dict = session.get('params')
        if not params_dict:
            return "Error: Params missing in session", 400

        # ACTUALIZACIÓN DE TODOS LOS PARÁMETROS DEL FORMULARIO

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

        # Feature cardinality y attach_prob (si tu generador los soporta)
        params_dict['PROB_FEATURE_CARDINALITY'] = float(request.form.get('prob_fc', 0.05))
        params_dict['MIN_FEATURE_CARDINALITY'] = [int(request.form.get('fc_min_min', 1)), int(request.form.get('fc_max_min', 1))]
        params_dict['MAX_FEATURE_CARDINALITY'] = [int(request.form.get('fc_min_max', 1)), int(request.form.get('fc_max_max', 1))]

        # Checkbox (nivel de lenguaje) – Boolean, Arithmetic, etc (si algún día habilitas)
        params_dict['GROUP_CARDINALITY'] = 'group_cardinality' in request.form
        # Los demás están disabled por ahora

        # Actualiza el objeto Params
        params = Params(**params_dict)
        session['params'] = params.__dict__

        return redirect(url_for('generator.step3'))

    current_step = 2
    return render_template('generator/step2.html', current_step=current_step)


@generator_bp.route('/generator/step3', methods=['GET', 'POST'])
def step3():
    if request.method == 'POST':
        params_dict = session.get('params')
        if not params_dict:
            return "Error: Params missing in session", 400

        # Recoge todos los parámetros de constraints
        params_dict['MIN_CONSTRAINTS'] = int(request.form.get('num_constraints_min', 0))
        params_dict['MAX_CONSTRAINTS'] = int(request.form.get('num_constraints_max', 0))
        params_dict['EXTRA_CONSTRAINT_REPRESENTATIVENESS'] = float(request.form.get('extra_constraint_repr', 0.7))

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

        # Genera los modelos y el zip
        # temp_dir = tempfile.mkdtemp()
        # output_dir = os.path.join(temp_dir, "models_output")
        # os.makedirs(output_dir, exist_ok=True)
        # fm_generator = FmgeneratorModel(params)
        # fm_generator.generate_models(output_dir)
        # zip_path = os.path.join(temp_dir, "feature_models.zip")
        # generator_service.zip_generated_models(output_dir, zip_path)
        # zip_filename = f"fms.zip"
        # try:
        #     return send_file(zip_path, as_attachment=True, download_name=zip_filename)
        # finally:
        #     if os.path.exists(temp_dir):
        #         shutil.rmtree(temp_dir)

        return redirect(url_for('generator.step4'))

    current_step = 3
    return render_template('generator/step3.html', current_step=current_step)


from flamapy.metamodels.fm_metamodel.models.feature_model import Attribute, Domain, Range

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
            params_dict['ATTRIBUTES_LIST'] = []
            params_dict['ATTRIBUTE_ATTACH_PROBS'] = []
            params_dict['ATTRIBUTE_IN_CONSTRAINTS'] = []
        else:
            attr_names = request.form.getlist('attr_name')
            attr_types = request.form.getlist('attr_type')
            attr_defaults = request.form.getlist('attr_value')
            attr_attach_probs = request.form.getlist('attr_attach_prob')
            attr_use_in_constraints = request.form.getlist('attr_use_in_constraints')

            attributes_list = []
            attach_probs_list = []
            in_constraints_list = []

            # Ajusta esto según cómo llega el checkbox en el request (para "use in constraints")
            constraints_checked = set()
            for idx, val in enumerate(attr_use_in_constraints):
                if val == 'on' or val == str(idx):
                    constraints_checked.add(idx)

            for i in range(len(attr_names)):
                name = attr_names[i]
                type_ = attr_types[i].lower()
                default_value = attr_defaults[i]

                # --- Domain y default_value según tipo ---
                if type_ == "boolean":
                    domain = Domain(ranges=None, elements=[True, False])
                    default_value = True if default_value == "True" else False
                elif type_ == "integer":
                    domain = Domain(ranges=None, elements=None)
                    default_value = int(default_value) if default_value else 0
                elif type_ == "real":
                    domain = Domain(ranges=None, elements=None)
                    default_value = float(default_value) if default_value else 0.0
                elif type_ == "string":
                    domain = Domain(ranges=None, elements=None)
                    # default_value already string
                else:
                    domain = Domain(ranges=None, elements=None)

                attribute = Attribute(
                    name=name,
                    domain=domain,
                    default_value=default_value
                )
                attributes_list.append(attribute)
                attach_probs_list.append(float(attr_attach_probs[i]) if attr_attach_probs[i] else 1.0)
                # "on" is present in attr_use_in_constraints if checked, else it's absent
                in_constraints_list.append(i in constraints_checked)

            params_dict['MIN_ATTRIBUTES'] = None
            params_dict['MAX_ATTRIBUTES'] = None
            params_dict['ATTRIBUTES_LIST'] = attributes_list
            params_dict['ATTRIBUTE_ATTACH_PROBS'] = attach_probs_list
            params_dict['ATTRIBUTE_IN_CONSTRAINTS'] = in_constraints_list

        params = Params(**params_dict)
        session['params'] = params.__dict__

        print(params)

        # Genera modelos y zip
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

    current_step = 4
    return render_template('generator/step4.html', current_step=current_step)
