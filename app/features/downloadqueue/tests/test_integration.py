import pytest

pytestmark = pytest.mark.integration


def test_downloadqueue_page_renders_with_no_files(test_client):
    assert test_client.get("/downloadqueue").status_code == 200


def test_download_build_returns_a_zip(test_client):
    response = test_client.get("/dataset/build/download/?files=")

    assert response.status_code == 200
    assert response.mimetype == "application/zip"
