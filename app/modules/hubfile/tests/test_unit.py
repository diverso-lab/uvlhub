from unittest.mock import patch

from app.modules.featuremodel.repositories import FeatureModelRepository
from app.modules.hubfile.repositories import HubfileRepository
from app.modules.dataset.repositories import DataSetRepository
from app.modules.dataset.repositories import DSMetaDataRepository
from app.modules.dataset.models import PublicationType
from app.modules.auth.repositories import UserRepository


def test_create_hubfile_call_publish_event(test_client):
    with patch("app.modules.event.services.EventService.publish") as mock_publish:
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
        mock_publish.assert_called_once_with(
            "events",
            "hubfile_created",
            {"path": f"uploads/user_{user.id}/dataset_{dataset.id}/test.uvl"},
        )
