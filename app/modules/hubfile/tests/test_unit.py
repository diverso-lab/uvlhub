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
        assert mock_enqueue_task.call_count == 3

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


def test_explore_hubfile_view_link_uses_result_url(test_client):
    response = test_client.get("/explore")
    assert response.status_code == 200
    html = response.data.decode()
    start = html.index('<script id="hubfile-template"')
    end = html.index("</script>", start)
    hubfile_block = html[start:end]

    assert 'href="/hubfiles/[[id]]"' not in hubfile_block
    assert 'href="/hubfiles/download/[[id]]"' in hubfile_block
    assert 'href="[[url]]"' in hubfile_block
