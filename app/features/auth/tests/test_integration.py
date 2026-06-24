from unittest.mock import patch

import pytest
from flask import url_for

pytestmark = pytest.mark.integration

NEXT_URL = "/dataset/import/?import=https://www.uvlhub.io/doi/10.5281/zenodo.1/files/raw/editor_model.uvl"


def _logout(test_client):
    test_client.get("/logout", follow_redirects=True)


# --- login ---------------------------------------------------------------


def test_login_succeeds_with_valid_credentials(test_client):
    response = test_client.post(
        "/login", data=dict(email="test@example.com", password="test1234"), follow_redirects=True
    )

    assert response.request.path != url_for("auth.login")
    _logout(test_client)


def test_login_redirects_to_next_when_present(test_client):
    response = test_client.post(
        f"/login?next={NEXT_URL}",
        data=dict(email="test@example.com", password="test1234", next=NEXT_URL),
        follow_redirects=False,
    )

    assert response.status_code in (301, 302)
    assert response.headers["Location"].endswith(NEXT_URL)
    _logout(test_client)


def test_login_ignores_an_unsafe_next_url(test_client):
    response = test_client.post(
        "/login?next=https://evil.example.com",
        data=dict(email="test@example.com", password="test1234", next="https://evil.example.com"),
        follow_redirects=False,
    )

    assert response.status_code in (301, 302)
    assert response.headers["Location"].endswith(url_for("public.index"))
    _logout(test_client)


def test_login_fails_with_an_unknown_email(test_client):
    _logout(test_client)
    response = test_client.post(
        "/login", data=dict(email="nobody@example.com", password="test1234"), follow_redirects=True
    )

    assert response.request.path == url_for("auth.login")


def test_login_fails_with_a_wrong_password(test_client):
    _logout(test_client)
    response = test_client.post(
        "/login", data=dict(email="test@example.com", password="wrong-password"), follow_redirects=True
    )

    assert response.request.path == url_for("auth.login")


# --- signup --------------------------------------------------------------


def test_signup_requires_the_name(test_client):
    _logout(test_client)
    response = test_client.post(
        "/signup", data=dict(surname="Foo", email="test@example.com", password="test1234"), follow_redirects=True
    )

    assert response.request.path == url_for("auth.signup")
    assert b"This field is required" in response.data


@patch("app.features.auth.routes.captcha_service.validate_captcha", return_value=True)
def test_signup_fails_when_passwords_do_not_match(_captcha, test_client):
    _logout(test_client)
    response = test_client.post(
        "/signup/",
        data=dict(name="Test", surname="Foo", email="test@example.com", password="test1234", captcha="x"),
        follow_redirects=True,
    )

    assert response.request.path == url_for("auth.signup")


@patch("app.features.auth.routes.captcha_service.validate_captcha", return_value=True)
def test_signup_succeeds_and_logs_the_user_in(_captcha, test_client):
    _logout(test_client)
    response = test_client.post(
        "/signup/",
        data=dict(
            name="Foo",
            surname="Example",
            email="foo@example.com",
            password="foo1234",
            confirm_password="foo1234",
            captcha="x",
        ),
        follow_redirects=True,
    )

    assert response.request.path == url_for("public.index")
    _logout(test_client)


@patch("app.features.auth.routes.captcha_service.validate_captcha", return_value=True)
def test_signup_redirects_to_next_when_present(_captcha, test_client):
    _logout(test_client)
    response = test_client.post(
        f"/signup/?next={NEXT_URL}",
        data=dict(
            name="Foo",
            surname="Example",
            email="foo-next@example.com",
            password="foo1234",
            confirm_password="foo1234",
            captcha="x",
            next=NEXT_URL,
        ),
        follow_redirects=False,
    )

    assert response.status_code in (301, 302)
    assert response.headers["Location"].endswith(NEXT_URL)
    _logout(test_client)


@patch("app.features.auth.services.TaskQueueManager.enqueue_task")
@patch("app.features.auth.routes.captcha_service.validate_captcha", return_value=True)
def test_signup_enqueues_the_confirmation_email(_captcha, enqueue, test_client):
    _logout(test_client)
    test_client.post(
        "/signup/",
        data=dict(
            name="Test",
            surname="Foo",
            email="confirm@example.com",
            password="test1234",
            confirm_password="test1234",
            captcha="x",
        ),
        follow_redirects=True,
    )

    enqueue.assert_called_once()
    assert enqueue.call_args.kwargs["email"] == "confirm@example.com"
    _logout(test_client)


# --- flamapyIDE auth status ---------------------------------------------


def test_auth_status_requires_authentication(test_client):
    _logout(test_client)
    response = test_client.get("/api/v1/auth/status")

    assert response.status_code == 401
    payload = response.get_json()
    assert payload["authenticated"] is False
    assert {"login_url", "signup_url", "orcid_url"} <= payload.keys()


def test_auth_status_returns_the_user_when_authenticated(test_client):
    _logout(test_client)
    test_client.post("/login", data=dict(email="test@example.com", password="test1234"), follow_redirects=True)

    response = test_client.get("/api/v1/auth/status")

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["authenticated"] is True
    assert payload["user"]["email"] == "test@example.com"
    _logout(test_client)
