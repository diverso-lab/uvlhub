import os
import shutil

from dotenv import load_dotenv

from app.modules.auth.models import User
from app.modules.dataset.models import Author, DataSet, DSMetaData, DSMetrics, PublicationType
from app.modules.featuremodel.models import FeatureModel
from app.modules.hubfile.models import Hubfile
from core.seeders.BaseSeeder import BaseSeeder


class DataSetSeeder(BaseSeeder):

    priority = 2  # Lower priority

    def run(self):
        # Retrieve users
        user1 = User.query.filter_by(email="user1@example.com").first()
        user2 = User.query.filter_by(email="user2@example.com").first()

        if not user1 or not user2:
            raise Exception("Users not found. Please seed users first.")

        # Create DSMetrics instance
        ds_metrics = DSMetrics(number_of_models=5, number_of_features=50)
        seeded_ds_metrics = self.seed([ds_metrics])[0]

        # Create DSMetaData instances
        ds_meta_data_list = [
            DSMetaData(
                deposition_id=1 + i,
                title=f"Sample dataset {i+1}",
                description=f"Description for dataset {i+1}",
                publication_type=PublicationType.DATA_MANAGEMENT_PLAN,
                publication_doi=f"https://www.doi.org/10.1234/dataset{i+1}",
                dataset_doi=f"10.1234/dataset{i+1}",
                tags="tag1, tag2",
                ds_metrics_id=seeded_ds_metrics.id,
            )
            for i in range(4)
        ]
        seeded_ds_meta_data = self.seed(ds_meta_data_list)

        # Create Author instances and associate with DSMetaData
        authors = [
            Author(
                name=f"Author {i+1}",
                affiliation=f"Affiliation {i+1}",
                orcid=f"0000-0000-0000-000{i}",
                ds_meta_data_id=seeded_ds_meta_data[i % 4].id,
            )
            for i in range(4)
        ]
        self.seed(authors)

        # Create DataSet instances
        datasets = [
            DataSet(
                user_id=user1.id if i % 2 == 0 else user2.id,
                ds_meta_data_id=seeded_ds_meta_data[i].id,
                feature_model_count=3,
            )
            for i in range(4)
        ]
        seeded_datasets = self.seed(datasets)

        # Create FeatureModels (3 por dataset → 4 datasets × 3 = 12)
        feature_models = [
            FeatureModel(
                dataset_id=seeded_datasets[i // 3].id,
            )
            for i in range(12)
        ]
        seeded_feature_models = self.seed(feature_models)

        # Crear archivos y Hubfiles
        load_dotenv()
        working_dir = os.getenv("WORKING_DIR", "")
        src_folder = os.path.join(working_dir, "app", "modules", "dataset", "uvl_examples")

        for i in range(12):
            file_name = f"file{i+1}.uvl"
            feature_model = seeded_feature_models[i]
            dataset = next(ds for ds in seeded_datasets if ds.id == feature_model.dataset_id)
            user_id = dataset.user_id

            dest_folder = os.path.join(
                working_dir,
                "uploads",
                f"user_{user_id}",
                f"dataset_{dataset.id}",
                "uvl",
            )
            os.makedirs(dest_folder, exist_ok=True)
            src_path = os.path.join(src_folder, file_name)
            dest_path = os.path.join(dest_folder, file_name)

            shutil.copy(src_path, dest_path)

            uvl_file = Hubfile(
                name=file_name,
                checksum=f"checksum{i+1}",  # Puedes calcularlo si quieres con hashlib
                size=os.path.getsize(dest_path),
                feature_model_id=feature_model.id,
            )

            self.seed([uvl_file])
