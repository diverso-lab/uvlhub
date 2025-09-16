import time
from unittest.mock import patch

import pytest
from flask import url_for

from app import mail_service
from app.modules.auth.repositories import UserRepository
from app.modules.auth.services import AuthenticationService
from app.modules.confirmemail.services import ConfirmemailService
from app.modules.profile.repositories import UserProfileRepository


@pytest.fixture(scope="module")
def test_client(test_client):
    """
    Extends the test_client fixture to add additional specific data for module testing.
    """
    with test_client.application.app_context():
        # Add HERE new elements to the database that you want to exist in the test context.
        # DO NOT FORGET to use db.session.add(<element>) and db.session.commit() to save the data.
        pass

    yield test_client


def test_login_success(test_client):
    response = test_client.post(
        "/login",
        data=dict(email="test@example.com", password="test1234"),
        follow_redirects=True,
    )

    assert response.request.path != url_for("auth.login"), "Login was unsuccessful"

    test_client.get("/logout", follow_redirects=True)


def test_login_unsuccessful_bad_email(test_client):
    response = test_client.post(
        "/login",
        data=dict(email="bademail@example.com", password="test1234"),
        follow_redirects=True,
    )

    assert response.request.path == url_for("auth.login"), "Login was unsuccessful"

    test_client.get("/logout", follow_redirects=True)


def test_login_unsuccessful_bad_password(test_client):
    response = test_client.post(
        "/login",
        data=dict(email="test@example.com", password="basspassword"),
        follow_redirects=True,
    )

    assert response.request.path == url_for("auth.login"), "Login was unsuccessful"

    test_client.get("/logout", follow_redirects=True)


def test_signup_user_no_name(test_client):
    response = test_client.post(
        "/signup",
        data=dict(surname="Foo", email="test@example.com", password="test1234"),
        follow_redirects=True,
    )
    assert response.request.path == url_for("auth.signup"), "Signup was unsuccessful"
    assert b"This field is required" in response.data, response.data


@patch("app.modules.captcha.services.CaptchaService.validate_captcha", return_value=True)
def test_signup_user_unsuccessful(mock_captcha, test_client):
    email = "test@example.com"
    response = test_client.post(
        "/signup/",
        data=dict(
            name="Test",
            surname="Foo",
            email=email,
            password="test1234",
            captcha="dummy_captcha",
        ),
        follow_redirects=True,
    )
    assert response.request.path == url_for("auth.signup"), "Signup was unsuccessful"


@patch("app.modules.captcha.services.CaptchaService.validate_captcha", return_value=True)
def test_signup_user_successful(mock_captcha, test_client):
    response = test_client.post(
        "/signup/",
        data=dict(
            name="Foo",
            surname="Example",
            email="foo@example.com",
            password="foo1234",
            captcha="dummy_captcha",
        ),
        follow_redirects=True,
    )
    assert response.request.path == url_for("public.index"), "Signup was unsuccessful"


def test_service_create_with_profie_success(clean_database):
    data = {
        "name": "Test",
        "surname": "Foo",
        "email": "service_test@example.com",
        "password": "test1234",
    }

    AuthenticationService().create_with_profile(**data)

    assert UserRepository().count() == 1
    assert UserProfileRepository().count() == 1


def test_service_create_with_profile_fail_no_email(clean_database):
    data = {"name": "Test", "surname": "Foo", "email": "", "password": "1234"}

    with pytest.raises(ValueError, match="Email is required."):
        AuthenticationService().create_with_profile(**data)

    assert UserRepository().count() == 0
    assert UserProfileRepository().count() == 0


def test_service_create_with_profile_fail_no_password(clean_database):
    data = {
        "name": "Test",
        "surname": "Foo",
        "email": "test@example.com",
        "password": "",
    }

    with pytest.raises(ValueError, match="Password is required."):
        AuthenticationService().create_with_profile(**data)

    assert UserRepository().count() == 0
    assert UserProfileRepository().count() == 0


@patch("app.modules.captcha.services.CaptchaService.validate_captcha", return_value=True)
def test_signup_send_confirmation_email(mock_captcha, test_client, clean_database):
    data = {
        "name": "Test",
        "surname": "Foo",
        "email": "test_confirmation@example.com",
        "password": "test1234",
        "captcha": "dummy_captcha",
    }

    with mail_service.mail.record_messages() as outbox:
        test_client.post("/signup", data=data, follow_redirects=True)
        assert len(outbox) == 1


def test_create_with_profile_create_inactive_user(test_client, clean_database):
    data = {
        "name": "Test",
        "surname": "Foo",
        "email": "user@example.com",
        "password": "test1234",
    }
    user = AuthenticationService().create_with_profile(**data)
    assert UserRepository().count() == 1
    assert UserProfileRepository().count() == 1
    assert user.active is False


def test_confirm_user_token_expired(test_client):
    email = "expired@example.com"

    with patch(
        "time.time",
        return_value=time.time() - (ConfirmemailService().CONFIRM_EMAIL_TOKEN_MAX_AGE + 1),
    ):
        token = ConfirmemailService().get_token_from_email(email)

    url = url_for("confirmemail.confirm_user", token=token, _external=False)
    response = test_client.get(url, follow_redirects=True)
    assert response.request.path == url_for("auth.signup", _external=False)


def test_confirm_user_token_tempered(test_client):
    email = "expired@example.com"

    AuthenticationService.SALT = "bad_salt"
    token = ConfirmemailService().get_token_from_email(email)

    AuthenticationService.SALT = "user-confirm"
    url = url_for("confirmemail.confirm_user", token=token, _external=False)
    response = test_client.get(url, follow_redirects=True)
    assert response.request.path == url_for("auth.signup", _external=False)


def test_confirm_user_active_user(test_client):
    data = {
        "name": "Test",
        "surname": "Foo",
        "email": "user@example.com",
        "password": "test1234",
    }
    user = AuthenticationService().create_with_profile(**data)
    assert user.active is False

    token = ConfirmemailService().get_token_from_email(user.email)

    url = url_for("confirmemail.confirm_user", token=token, _external=False)
    response = test_client.get(url, follow_redirects=True)
    assert response.request.path == url_for("public.index", _external=False)

    user = UserRepository().get_by_email(user.email)
    assert user.active is True
