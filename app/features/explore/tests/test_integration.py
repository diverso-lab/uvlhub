import pytest

pytestmark = pytest.mark.integration


def test_explore_page_renders(test_client):
    assert test_client.get("/explore").status_code == 200
