import pytest

pytestmark = pytest.mark.integration


def test_zenodo_index_renders(test_client):
    assert test_client.get("/zenodo").status_code == 200
