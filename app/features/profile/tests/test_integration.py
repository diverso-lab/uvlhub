import pytest

pytestmark = pytest.mark.integration


def _login(test_client):
    test_client.post("/login", data=dict(email="test@example.com", password="test1234"), follow_redirects=True)


def test_summary_requires_login(test_client):
    test_client.get("/logout", follow_redirects=True)

    response = test_client.get("/profile/summary")

    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_edit_profile_page_renders_for_an_authenticated_user(test_client):
    _login(test_client)

    response = test_client.get("/profile/edit")

    assert response.status_code == 200
    assert b"Edit profile" in response.data
    test_client.get("/logout", follow_redirects=True)


def test_summary_renders_for_an_authenticated_user(test_client):
    _login(test_client)

    assert test_client.get("/profile/summary").status_code == 200
    test_client.get("/logout", follow_redirects=True)


def test_api_me_returns_the_profile_for_an_authenticated_user(test_client):
    _login(test_client)

    response = test_client.get("/api/me")

    assert response.status_code == 200
    assert response.get_json()["name"] == "Test"
    test_client.get("/logout", follow_redirects=True)
