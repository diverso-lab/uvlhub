import pytest

pytestmark = pytest.mark.integration


def test_view_factlabel_returns_404_for_an_unknown_file(test_client):
    assert test_client.get("/factlabel/view/999999").status_code == 404
