import pytest

pytestmark = pytest.mark.integration


def test_mail_index_renders(test_client):
    assert test_client.get("/mail").status_code == 200
