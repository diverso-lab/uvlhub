import os
from zipfile import ZipFile

from app.modules.generator.repositories import GeneratorRepository
from core.services.BaseService import BaseService


class GeneratorService(BaseService):
    def __init__(self):
        super().__init__(GeneratorRepository())

    def zip_generated_models(self, output_dir, zip_path):
        with ZipFile(zip_path, "w") as zipf:
            for root, dirs, files in os.walk(output_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, output_dir)
                    zipf.write(file_path, arcname=arcname)
