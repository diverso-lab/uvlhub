import logging
import os
import shutil

from app import db
from app.modules.featuremodel.models import FeatureModel
from app.modules.featuremodel.repositories import FeatureModelRepository
from app.modules.hubfile.services import HubfileService
from core.services.BaseService import BaseService

logger = logging.getLogger(__name__)


class FeatureModelService(BaseService):
    def __init__(self):
        super().__init__(FeatureModelRepository())
        self.hubfile_service = HubfileService()

    def total_feature_model_views(self) -> int:
        return self.hubfile_service.total_hubfile_views()

    def total_feature_model_downloads(self) -> int:
        return self.hubfile_service.total_hubfile_downloads()

    def count_feature_models(self):

        from app.modules.dataset.services import DataSetService

        dataset_service = DataSetService()
        synchronized_datasets = dataset_service.get_synchronized_datasets()

        total_feature_models = sum(dataset.feature_model_count for dataset in synchronized_datasets)

        return total_feature_models

    def create_from_uvl_files(self, dataset, base_dir: str = None) -> list[FeatureModel]:
        """
        Crea un FeatureModel y Hubfile por cada archivo UVL en el directorio indicado.
        Si no se pasa base_dir, se usan los UVL del directorio temporal del usuario.

        Args:
            dataset (DataSet): Dataset al que se van a asociar los modelos.
            base_dir (str, opcional): Directorio desde el que leer los UVL.

        Returns:
            list[FeatureModel]: Lista de modelos creados.
        """
        user = dataset.user
        source_dir = base_dir or user.temp_folder()  # 👈 aquí el cambio

        working_dir = os.getenv("WORKING_DIR", "")
        dest_dir = os.path.join(
            working_dir,
            "uploads",
            f"user_{user.id}",
            f"dataset_{dataset.id}",
            "uvl",
        )
        os.makedirs(dest_dir, exist_ok=True)

        created_models = []
        hubfile_service = HubfileService()

        for filename in os.listdir(source_dir):
            if not filename.endswith(".uvl"):
                continue

            uvl_path = os.path.join(source_dir, filename)
            original_filename = filename.split("_", 1)[-1] if "_" in filename else filename

            dest_path = os.path.join(dest_dir, original_filename)
            shutil.move(uvl_path, dest_path)
            logger.info(f"[FM] Moved {filename} to {dest_path}")

            feature_model = FeatureModel(dataset_id=dataset.id)
            db.session.add(feature_model)
            db.session.flush()

            hubfile = hubfile_service.create_from_file(feature_model.id, dest_path)
            logger.info(f"[FM] Hubfile created with ID: {hubfile.id} for FeatureModel {feature_model.id}")

            created_models.append(feature_model)

        db.session.commit()
        logger.info(f"[FM] {len(created_models)} feature models created for dataset {dataset.id}")

        return created_models
