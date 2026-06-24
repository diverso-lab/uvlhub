import pytest

pytestmark = pytest.mark.integration


def test_featuremodel_index_renders(test_client):
    assert test_client.get("/featuremodel").status_code == 200
