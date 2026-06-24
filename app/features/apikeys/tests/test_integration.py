import pytest

pytestmark = pytest.mark.integration


def _login(test_client):
    test_client.post("/login", data=dict(email="test@example.com", password="test1234"), follow_redirects=True)


def test_index_is_public(test_client):
    test_client.get("/logout", follow_redirects=True)

    assert test_client.get("/apikeys").status_code == 200


def test_generate_requires_login(test_client):
    test_client.get("/logout", follow_redirects=True)

    response = test_client.get("/developer/api-keys/generate")

    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_generate_then_list_returns_ok(test_client):
    _login(test_client)

    generated = test_client.post("/developer/api-keys/generate", data={"scopes": "read_dataset"}, follow_redirects=True)
    listing = test_client.get("/developer/api-keys")

    assert generated.status_code == 200
    assert listing.status_code == 200
    test_client.get("/logout", follow_redirects=True)
