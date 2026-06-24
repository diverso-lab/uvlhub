import pytest
from flask import url_for

pytestmark = pytest.mark.integration


def test_forgot_page_renders_for_a_guest(test_client):
    test_client.get("/logout", follow_redirects=True)

    assert test_client.get("/reset/forgot").status_code == 200


def test_forgot_post_redirects_to_login(test_client):
    test_client.get("/logout", follow_redirects=True)

    response = test_client.post("/reset/forgot", data={"email": "test@example.com"}, follow_redirects=False)

    assert response.status_code in (301, 302)
    assert response.headers["Location"].endswith(url_for("auth.login"))


def test_reset_password_with_invalid_token_returns_404(test_client):
    test_client.get("/logout", follow_redirects=True)

    assert test_client.get("/reset/password/clearly-not-a-valid-token").status_code == 404
