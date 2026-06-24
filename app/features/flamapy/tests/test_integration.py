import pytest

pytestmark = pytest.mark.integration


def test_valid_endpoint_returns_success(test_client):
    response = test_client.get("/flamapy/valid/42")

    assert response.status_code == 200
    assert response.get_json() == {"success": True, "file_id": 42}


def test_to_glencoe_returns_404_for_an_unknown_file(test_client):
    assert test_client.get("/flamapy/to_glencoe/999999").status_code == 404
