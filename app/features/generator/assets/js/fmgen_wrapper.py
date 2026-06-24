# fmgen_wrapper.py — runs inside Pyodide and returns generated UVL strings.
#
# Two entry points:
#
#   generate_models(params_json)               -> JSON list of UVL strings
#       One-shot generation; used by the backend tests. Not great for UIs
#       because the caller gets no progress updates until everything is done.
#
#   generate_one_model(params_json, index)     -> JSON object {filename, content}
#       Generate a single model at the given index. The JS side loops over
#       0..NUM_MODELS-1 and updates the progress bar between iterations, so
#       the user sees "Generating N / M" instead of a frozen modal.

import json
import os
import shutil
import tempfile

from flamapy.metamodels.fm_metamodel.transformations.uvl_writer import UVLWriter
from fm_generator.FMGenerator.models.config import Params
from fm_generator.FMGenerator.models.models import FmgeneratorModel


def generate_models(params_json: str) -> str:
    """Generate the full batch and return every UVL as a JSON list."""
    params_dict = json.loads(params_json)
    params = Params(**params_dict)

    temp_dir = tempfile.mkdtemp()
    output_dir = os.path.join(temp_dir, "models_output")
    os.makedirs(output_dir, exist_ok=True)

    try:
        FmgeneratorModel(params).generate_models(output_dir)
        results = []
        for fname in sorted(os.listdir(output_dir)):
            if fname.endswith(".uvl"):
                with open(os.path.join(output_dir, fname), "r", encoding="utf-8") as f:
                    results.append(f.read())
        return json.dumps(results)
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def generate_one_model(params_json: str, index: int) -> str:
    """Generate the model at `index` and return {filename, content} as JSON.

    The caller (scripts.js) iterates from 0 to NUM_MODELS-1, updating the
    progress bar each time. Each call is deterministic given (SEED, index)
    and honours ENSURE_SATISFIABLE/filename-suffix options.
    """
    params_dict = json.loads(params_json)
    params = Params(**params_dict)
    gen = FmgeneratorModel(params)

    temp_dir = tempfile.mkdtemp()
    try:
        fm = gen._build_one(int(index))
        filename = gen._filename_for(fm, int(index))
        output_file = os.path.join(temp_dir, filename)
        UVLWriter(output_file, fm).transform()
        with open(output_file, "r", encoding="utf-8") as f:
            content = f.read()
        return json.dumps(
            {
                "filename": filename,
                "content": content,
                "features": len(list(fm.get_features())),
                "constraints": len(fm.ctcs),
            }
        )
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
