import pytest

pytestmark = pytest.mark.integration


def test_elasticsearch_index_renders(test_client):
    assert test_client.get("/elasticsearch").status_code == 200
