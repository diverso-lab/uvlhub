import hashlib
import os
import shutil
import uuid
import zipfile
from pathlib import Path
from typing import List, Tuple

from flask import jsonify, request
from flask_login import current_user

from app import db
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

        hubfile = Hubfile(feature_model_id=feature_model_id, name=name, size=size, checksum=checksum)
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

        existing_record = self.the_record_exists(hubfile=hubfile, user_cookie=user_cookie)

        if not existing_record:
            self.create_new_record(hubfile=hubfile, user_cookie=user_cookie)
            self.statistics_service.increment_feature_models_downloaded()

        return user_cookie


class UploadIngestService:
    """
    Prepara los UVL para su procesamiento:
      - Extrae zips de forma segura.
      - Recolecta todos los .uvl (de zips y sueltos).
      - Aplana en una carpeta de staging.
    """

    def __init__(self, logger):
        self.logger = logger

    # -------- utils -------- #

    def _safe_extract_zip(self, zip_path: str, dest_dir: str) -> None:
        """Extrae evitando path traversal."""
        with zipfile.ZipFile(zip_path, "r") as zf:
            for member in zf.infolist():
                # Normaliza y evita rutas absolutas o con ..
                member_path = Path(member.filename)
                if member.is_dir():
                    continue
                target_path = Path(dest_dir) / member_path
                # Comprobación de contención
                target_path_resolved = target_path.resolve()
                if not str(target_path_resolved).startswith(str(Path(dest_dir).resolve())):
                    raise ValueError(f"[INGEST] Zip slip detectado en {zip_path}: {member.filename}")
                target_path.parent.mkdir(parents=True, exist_ok=True)
                with zf.open(member, "r") as src, open(target_path, "wb") as dst:
                    shutil.copyfileobj(src, dst)

    def _unique_dest(self, dest_dir: str, filename: str) -> str:
        """Genera un nombre único si hay colisiones."""
        base = Path(filename).stem
        ext = Path(filename).suffix
        candidate = Path(dest_dir) / f"{base}{ext}"
        i = 1
        while candidate.exists():
            candidate = Path(dest_dir) / f"{base} ({i}){ext}"
            i += 1
        return str(candidate)

    # -------- public -------- #

    def prepare_uvls(self, temp_root: str) -> Tuple[str, List[str]]:
        """
        Prepara y aplana UVLs en temp_root/_uvl_stage.
        Devuelve (stage_dir, lista_uvls).
        """
        stage_dir = str(Path(temp_root) / "_uvl_stage")
        extract_root = str(Path(temp_root) / "_extracted_zips")

        # Limpia staging/extract anteriores
        shutil.rmtree(stage_dir, ignore_errors=True)
        shutil.rmtree(extract_root, ignore_errors=True)
        Path(stage_dir).mkdir(parents=True, exist_ok=True)
        Path(extract_root).mkdir(parents=True, exist_ok=True)

        # 1) localizar y extraer zips
        zip_paths = [str(p) for p in Path(temp_root).rglob("*.zip")]
        self.logger.info(f"[INGEST] Zips detectados: {len(zip_paths)}")
        for zp in zip_paths:
            subdir = Path(extract_root) / f"{Path(zp).stem}_{uuid.uuid4().hex[:8]}"
            subdir.mkdir(parents=True, exist_ok=True)
            self._safe_extract_zip(zp, str(subdir))
            self.logger.info(f"[INGEST] Extraído: {zp} -> {subdir}")

        # 2) recolectar todos los .uvl (en temp_root y en extract_root)
        def collect_uvls_from(root: str) -> List[Path]:
            return [p for p in Path(root).rglob("*.uvl") if p.is_file()]

        uvl_sources = collect_uvls_from(temp_root) + collect_uvls_from(extract_root)
        self.logger.info(f"[INGEST] UVLs encontrados (antes de aplanar): {len(uvl_sources)}")

        # 3) aplanar en stage_dir con nombres únicos
        staged_paths: List[str] = []
        for src in uvl_sources:
            dest = self._unique_dest(stage_dir, src.name)
            shutil.copy2(str(src), dest)
            staged_paths.append(dest)

        # 4) validación mínima
        if not staged_paths:
            raise ValueError("No se encontró ningún archivo .uvl tras procesar zips y sueltos.")

        self.logger.info(f"[INGEST] UVLs en staging: {len(staged_paths)} (dir: {stage_dir})")
        return stage_dir, sorted(staged_paths)
