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


# Paso 1: mostrar formulario o recibir datos del formulario
@generator_bp.route('/generator/step1', methods=['GET', 'POST'])
def step1():
    if request.method == 'POST':
        # Recoge los datos del formulario como antes
        params = Params(
            NUM_MODELS = int(request.form.get('num_models_val', 0)),
            SEED = int(request.form.get('seed', 42)),
            ENSURE_SATISFIABLE = 'ensure_satisfiable' in request.form,
            NAME_PREFIX = request.form.get('name_prefix', ''),
            INCLUDE_FEATURE_COUNT_SUFFIX = 'feature_count_suffix' in request.form,
            INCLUDE_CONSTRAINT_COUNT_SUFFIX = 'constraint_count_suffix' in request.form,
        )
        session['params'] = params

        # Genera los modelos y el zip
        temp_dir = tempfile.mkdtemp()
        output_dir = os.path.join(temp_dir, "models_output")
        os.makedirs(output_dir, exist_ok=True)

        fm_generator = FmgeneratorModel(params)
        fm_generator.generate_models(output_dir)

        zip_path = os.path.join(temp_dir, "feature_models.zip")
        # Llama aquí al servicio para comprimir (asegúrate de tenerlo importado)
        generator_service.zip_generated_models(output_dir, zip_path)

        current_date = datetime.now().strftime("%Y_%m_%d")
        zip_filename = f"fms.zip"

        try:
            return send_file(zip_path, as_attachment=True, download_name=zip_filename)
        finally:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)

    # Si GET, renderiza el formulario normal
    current_step = 1
    return render_template('generator/step1.html', current_step=current_step)


# Paso 2 (de momento, solo muestra un placeholder)
# @generator_bp.route('/generator/step2', methods=['GET', 'POST'])
# def step2():
#     # if request.method == 'POST':
#         # params = session['params']
#         # params = Params(
#         #     NUM_MODELS = 55,
#         #     SEED = request.form.get('seed', 42),
#         #     ENSURE_SATISFIABLE = 'ensure_satisfiable' in request.form,
#         #     NAME_PREFIX = request.form.get('name_prefix', ''),
#         #     INCLUDE_FEATURE_COUNT_SUFFIX = 'feature_count_suffix' in request.form,
#         #     INCLUDE_CONSTRAINT_COUNT_SUFFIX = 'constraint_count_suffix' in request.form,
#         # )

#         # session['params'] = params
        
#         # print('')
#         # print(session['params'])
#         # print('')
#         # # REDIRIGIR AL PASO 3
#         # return redirect(url_for('generator.step2'))

#     current_step = 2
#     return render_template('generator/step2.html', current_step=current_step)
