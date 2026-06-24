import pytest

pytestmark = pytest.mark.unit

import os
from unittest.mock import patch

from dotenv import load_dotenv

from app.features.auth.repositories import UserRepository
from app.features.dataset.models import PublicationType
from app.features.dataset.repositories import DataSetRepository, DSMetaDataRepository
from app.features.featuremodel.repositories import FeatureModelRepository
from app.features.hubfile.repositories import HubfileRepository


def test_create_hubfile_calls_enqueue_tasks(test_client):
    with patch("app.managers.task_queue_manager.TaskQueueManager.enqueue_task") as mock_enqueue_task:
        # Create minimal entities
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

        # Verify call count
        assert mock_enqueue_task.call_count == 3

        # Verify transform_uvl was called
        mock_enqueue_task.assert_any_call(
            "app.features.hubfile.tasks.transform_uvl",
            path=path,
            timeout=5,
        )

        # Verify compute_factlabel was called
        mock_enqueue_task.assert_any_call(
            "app.features.hubfile.tasks.compute_factlabel",
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
