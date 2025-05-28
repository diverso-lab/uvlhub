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
        # params_dict['FC_MIN_VAL'] = int(request.form.get('fc_min_val', 1))
        # params_dict['FC_MIN_MAX'] = int(request.form.get('fc_min_max', 10))
        # params_dict['FC_MAX_MIN'] = int(request.form.get('fc_max_min', 1))
        # params_dict['FC_MAX_VAL'] = int(request.form.get('fc_max_val', 10))

        # Checkbox (nivel de lenguaje) – Boolean, Arithmetic, etc (si algún día habilitas)
        params_dict['GROUP_CARDINALITY'] = 'group_cardinality' in request.form
        # Los demás están disabled por ahora

        # Actualiza el objeto Params
        params = Params(**params_dict)
        session['params'] = params.__dict__

        print(params)

        # Lógica de generación y descarga
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

    current_step = 2
    return render_template('generator/step2.html', current_step=current_step)
