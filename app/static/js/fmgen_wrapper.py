import json
import os
import shutil
import tempfile

from fm_generator.FMGenerator.models.config import Params
from fm_generator.FMGenerator.models.models import FmgeneratorModel


def generate_models(params_json: str) -> str:
    """
    Wrapper que, dado un JSON con todos los params,
    genera los modelos y devuelve un JSON con una lista de objetos:
    [
        {"filename": "...", "content": "..."},
        ...
    ]
    """
    # 1) Parsear JSON de parámetros
    params_dict = json.loads(params_json)
    params = Params(**params_dict)

    # 2) Crear un directorio temporal donde se volcarán los .uvl
    temp_dir = tempfile.mkdtemp()
    output_dir = os.path.join(temp_dir, "models_output")
    os.makedirs(output_dir, exist_ok=True)

    # 3) Invocar generate_models con el directorio de salida
    fm_generator = FmgeneratorModel(params)
    fm_generator.generate_models(output_dir)

    # 4) Leer cada fichero .uvl y almacenar nombre + contenido
    results = []
    for fname in sorted(os.listdir(output_dir)):
        if fname.endswith(".uvl"):
            path = os.path.join(output_dir, fname)
            with open(path, "r", encoding="utf-8") as f:
                results.append({
                    "filename": fname,
                    "content": f.read(),
                })

    # 5) Limpiar el temporal
    shutil.rmtree(temp_dir)

    # 6) Devolver el JSON con todos los modelos
    return json.dumps(results)