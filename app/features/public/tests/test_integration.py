import pytest

pytestmark = pytest.mark.integration


def test_home_page_renders_with_statistics(test_client):
    response = test_client.get("/")

    assert response.status_code == 200
