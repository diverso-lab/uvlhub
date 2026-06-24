from unittest.mock import patch

import pytest

from app.features.auth.repositories import UserRepository
from app.features.dataset.models import PublicationType
from app.features.dataset.repositories import DataSetRepository, DSMetaDataRepository
from app.features.featuremodel.repositories import FeatureModelRepository
from app.features.hubfile.repositories import HubfileRepository

pytestmark = pytest.mark.integration


def _login(test_client):
    test_client.post("/login", data=dict(email="test@example.com", password="test1234"), follow_redirects=True)


def test_creating_a_hubfile_fans_out_to_the_domain_via_signal(test_client):
    # The generic hub only emits 'hubfile-created'; the UVL domain (flamapy +
    # factlabel) subscribes and enqueues its own processing.
    user = UserRepository().create(email="sig@example.com", password="pw-123456")
    meta = DSMetaDataRepository().create(title="t", description="d", publication_type=PublicationType.BOOK)
    dataset = DataSetRepository().create(user_id=user.id, ds_meta_data_id=meta.id)
    fm = FeatureModelRepository().create(dataset_id=dataset.id)

    with patch("app.managers.task_queue_manager.TaskQueueManager.enqueue_task") as enqueue:
        HubfileRepository().create(name="t.uvl", checksum="1", size=1, feature_model_id=fm.id)

    enqueued_tasks = [call.args[0] for call in enqueue.call_args_list]
    assert "app.features.flamapy.tasks.transform_uvl" in enqueued_tasks
    assert "app.features.factlabel.tasks.compute_factlabel" in enqueued_tasks
    assert enqueue.call_count == 3


def test_upload_requires_a_file(test_client):
    _login(test_client)

    response = test_client.post("/hubfile/upload", data={"uuid": "x"})

    assert response.status_code == 400
    test_client.get("/logout", follow_redirects=True)


def test_delete_requires_a_filename(test_client):
    _login(test_client)

    response = test_client.post("/hubfile/delete", json={})

    assert response.status_code == 400
    test_client.get("/logout", follow_redirects=True)


def test_clear_temp_succeeds_for_an_authenticated_user(test_client):
    _login(test_client)

    response = test_client.post("/hubfile/clear_temp")

    assert response.status_code == 200
    test_client.get("/logout", follow_redirects=True)


def test_explore_hubfile_template_links_use_the_result_url(test_client):
    response = test_client.get("/explore")

    assert response.status_code == 200
    html = response.data.decode()
    start = html.index('<script id="hubfile-template"')
    block = html[start : html.index("</script>", start)]
    assert 'href="/hubfiles/download/[[id]]"' in block
    assert 'href="[[url]]"' in block
