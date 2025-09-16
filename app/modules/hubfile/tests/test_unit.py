import os
from unittest.mock import patch

from dotenv import load_dotenv

from app.modules.auth.repositories import UserRepository
from app.modules.dataset.models import PublicationType
from app.modules.dataset.repositories import DataSetRepository, DSMetaDataRepository
from app.modules.featuremodel.repositories import FeatureModelRepository
from app.modules.hubfile.repositories import HubfileRepository


def test_create_hubfile_calls_enqueue_tasks(test_client):
    with patch("core.managers.task_queue_manager.TaskQueueManager.enqueue_task") as mock_enqueue_task:
        # Crear entidades mínimas
        user = UserRepository().create(password="foo")
        dsmetadata = DSMetaDataRepository().create(
            title="test",
            description="test",
            publication_type=PublicationType.BOOK,
        )
        dataset = DataSetRepository().create(user_id=user.id, ds_meta_data_id=dsmetadata.id)
        fm = FeatureModelRepository().create(dataset_id=dataset.id)
        hubfile = HubfileRepository().create(
            name="test.uvl",
            checksum="1234",
            size=1234,
            feature_model_id=fm.id,
        )

        load_dotenv()
        working_dir = os.getenv("WORKING_DIR", "")

        path = os.path.join(
            working_dir,
            "uploads",
            f"user_{user.id}",
            f"dataset_{dataset.id}",
            "uvl",
            "test.uvl",
        )

        # Verificar número de llamadas
        assert mock_enqueue_task.call_count == 2

        # Verificar que se llamó a transform_uvl
        mock_enqueue_task.assert_any_call(
            "app.modules.hubfile.tasks.transform_uvl",
            path=path,
            timeout=5,
        )

        # Verificar que se llamó a compute_factlabel
        mock_enqueue_task.assert_any_call(
            "app.modules.hubfile.tasks.compute_factlabel",
            hubfile_id=hubfile.id,
            timeout=5,
        )
