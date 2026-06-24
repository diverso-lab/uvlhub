import pytest

pytestmark = pytest.mark.integration


def test_team_page_renders(test_client):
    assert test_client.get("/team").status_code == 200
