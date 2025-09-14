import hashlib
import os
import shutil
import uuid

from flask import request, jsonify
from flask_login import current_user
from app.modules.auth.models import User
from app.modules.dataset.models import DataSet
from app.modules.hubfile.models import Hubfile
from app.modules.hubfile.repositories import (
    HubfileDownloadRecordRepository,
    HubfileRepository,
    HubfileViewRecordRepository,
)
from app.modules.statistics.services import StatisticsService
from core.services.BaseService import BaseService
from app import db


class HubfileService(BaseService):
    def __init__(self):
        super().__init__(HubfileRepository())
        self.hubfile_view_record_repository = HubfileViewRecordRepository()
        self.hubfile_download_record_repository = HubfileDownloadRecordRepository()

    def get_owner_user_by_hubfile(self, hubfile: Hubfile) -> User:
        return self.repository.get_owner_user_by_hubfile(hubfile)

    def get_dataset_by_hubfile(self, hubfile: Hubfile) -> DataSet:
        return self.repository.get_dataset_by_hubfile(hubfile)

    def get_path_by_hubfile(self, hubfile: Hubfile) -> str:

        hubfile_user = self.get_owner_user_by_hubfile(hubfile)
        hubfile_dataset = self.get_dataset_by_hubfile(hubfile)
        working_dir = os.getenv("WORKING_DIR")

        path = os.path.join(
            working_dir,
            "uploads",
            f"user_{hubfile_user.id}",
            f"dataset_{hubfile_dataset.id}",
            "uvl",
            hubfile.name,
        )

        return path

    def get_by_ids(self, ids: list[int]) -> list[Hubfile]:
        return self.repository.get_by_ids(ids)

    def create_from_file(self, feature_model_id: int, filepath: str) -> Hubfile:
        """
        Crea un Hubfile a partir de un archivo .uvl ya ubicado en el directorio destino.

        Args:
            feature_model_id (int): ID del FeatureModel al que pertenece el archivo.
            filepath (str): Ruta completa al archivo UVL.

        Returns:
            Hubfile: La instancia creada.
        """
        if not os.path.isfile(filepath):
            raise FileNotFoundError(f"Archivo no encontrado: {filepath}")

        name = os.path.basename(filepath)
        size = os.path.getsize(filepath)
        checksum = self._calculate_checksum(filepath)

        hubfile = Hubfile(
            feature_model_id=feature_model_id, name=name, size=size, checksum=checksum
        )
        db.session.add(hubfile)
        db.session.flush()

        return hubfile

    def _calculate_checksum(self, filepath: str) -> str:
        """Calcula el hash SHA256 del archivo"""
        sha256 = hashlib.sha256()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    def get_hubfile_url(self, hubfile: Hubfile) -> str:
        dataset = self.get_dataset_by_hubfile(hubfile)
        ds_meta = dataset.ds_meta_data
        if not ds_meta or not ds_meta.dataset_doi:
            return None

        path = f"/doi/{ds_meta.dataset_doi}/files/{hubfile.name}"

        return path
    
    def clear_temp(self):
        temp_folder = current_user.temp_folder()

        try:
            if os.path.exists(temp_folder):
                shutil.rmtree(temp_folder, ignore_errors=True)
            os.makedirs(temp_folder, exist_ok=True)

            return jsonify({"message": "Temp folder cleared"}), 200
        except Exception as e:
            return jsonify({"error": f"Error clearing temp folder: {str(e)}"}), 500


class HubfileDownloadRecordService(BaseService):
    def __init__(self):
        super().__init__(HubfileDownloadRecordRepository())
        self.statistics_service = StatisticsService()

    def the_record_exists(self, hubfile: Hubfile, user_cookie: str):
        return self.repository.the_record_exists(hubfile, user_cookie)

    def create_new_record(self, hubfile: Hubfile, user_cookie: str) -> Hubfile:
        return self.repository.create_new_record(hubfile, user_cookie)

    def create_cookie(self, hubfile: Hubfile):

        user_cookie = request.cookies.get("file_download_cookie")
        if not user_cookie:
            user_cookie = str(uuid.uuid4())

        existing_record = self.the_record_exists(
            hubfile=hubfile, user_cookie=user_cookie
        )

        if not existing_record:
            self.create_new_record(hubfile=hubfile, user_cookie=user_cookie)
            self.statistics_service.increment_feature_models_downloaded()

        return user_cookie
