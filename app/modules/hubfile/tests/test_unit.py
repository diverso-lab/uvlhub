import os
from unittest.mock import patch

from app.modules.featuremodel.repositories import FeatureModelRepository
from app.modules.hubfile.repositories import HubfileRepository
from app.modules.dataset.repositories import DataSetRepository
from app.modules.dataset.repositories import DSMetaDataRepository
from app.modules.dataset.models import PublicationType
from app.modules.auth.repositories import UserRepository
from dotenv import load_dotenv


def test_create_hubfile_calls_enqueue_task(test_client):
    with patch("core.managers.task_queue_manager.TaskQueueManager.enqueue_task") as mock_enqueue_task:
        user = UserRepository().create(password="foo")
        dsmetadata = DSMetaDataRepository().create(
            title="test",
            description="test",
            publication_type=PublicationType.BOOK,
        )
        dataset = DataSetRepository().create(user_id=user.id, ds_meta_data_id=dsmetadata.id)
        fm = FeatureModelRepository().create(data_set_id=dataset.id)
        HubfileRepository().create(
            name="test.uvl",
            checksum="1234",
            size=1234,
            feature_model_id=fm.id,
        )

        load_dotenv()
        working_dir = os.getenv('WORKING_DIR', '')

        path = os.path.join(
            working_dir,
            "uploads",
            f"user_{user.id}",
            f"dataset_{dataset.id}",
            "uvl",
            "test.uvl"
        )

        # Verificar que enqueue_task fue llamado correctamente
        mock_enqueue_task.assert_called_once_with(
            "app.modules.hubfile.tasks.transform_uvl",  # Nombre de la tarea
            path=path  # Parámetro que recibe la tarea
        )
