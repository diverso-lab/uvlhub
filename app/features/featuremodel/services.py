import logging
import os
import shutil

from splent_framework.services.BaseService import BaseService

from app.features.featuremodel.models import FeatureModel
from app.features.featuremodel.repositories import FeatureModelRepository
from app.features.hubfile.services import HubfileService

logger = logging.getLogger(__name__)


class FeatureModelService(BaseService):
    def __init__(self):
        super().__init__(FeatureModelRepository())
        self.hubfile_service = HubfileService()

    def count_feature_models(self) -> int:
        return self.repository.count_feature_models()

    def create_from_uvl_files(self, dataset, base_dir: str = None) -> list[FeatureModel]:
        """Create a FeatureModel and a Hubfile for every UVL file found.

        When ``base_dir`` is omitted the UVL files are taken from the owning
        user's temp folder. The whole batch is committed as a single unit of work.
        """
        user = dataset.user
        source_dir = base_dir or user.temp_folder()

        working_dir = os.getenv("WORKING_DIR", "")
        dest_dir = os.path.join(working_dir, "uploads", f"user_{user.id}", f"dataset_{dataset.id}", "uvl")
        os.makedirs(dest_dir, exist_ok=True)

        # Walk the staged tree so the folder structure the user uploaded is
        # preserved on disk and recorded on each Hubfile.
        created_models = []
        for subdir, _, files in os.walk(source_dir):
            rel_dir = os.path.relpath(subdir, source_dir)
            rel_dir = "" if rel_dir == "." else rel_dir.replace(os.sep, "/")

            for filename in sorted(files):
                if not filename.endswith(".uvl"):
                    continue

                dest_folder = os.path.join(dest_dir, *rel_dir.split("/")) if rel_dir else dest_dir
                os.makedirs(dest_folder, exist_ok=True)
                dest_path = os.path.join(dest_folder, filename)
                shutil.move(os.path.join(subdir, filename), dest_path)
                logger.info(f"[FM] Moved {rel_dir}/{filename} to {dest_path}")

                feature_model = self.repository.create(commit=False, dataset_id=dataset.id)
                hubfile = self.hubfile_service.create_from_file(
                    feature_model.id, dataset.id, dest_path, directory_path=rel_dir
                )
                logger.info(f"[FM] Hubfile {hubfile.id} created for FeatureModel {feature_model.id}")

                created_models.append(feature_model)

        self.repository.session.commit()
        logger.info(f"[FM] {len(created_models)} feature models created for dataset {dataset.id}")
        return created_models
