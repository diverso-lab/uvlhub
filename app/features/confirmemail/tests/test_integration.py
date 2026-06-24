import pytest
from flask import url_for

from app.features.auth.services import AuthenticationService
from app.features.confirmemail.services import ConfirmemailService

pytestmark = pytest.mark.integration


def test_confirm_user_with_a_valid_token_logs_in_and_redirects_home(test_client, clean_database):
    AuthenticationService().create_with_profile(
        name="Test", surname="User", email="valid@example.com", password="pw-123456"
    )
    token = ConfirmemailService().get_token_from_email("valid@example.com")

    response = test_client.get(url_for("confirmemail.confirm_user", token=token), follow_redirects=True)

    assert response.request.path == url_for("public.index")


def test_confirm_user_with_an_invalid_token_redirects_to_signup(test_client):
    # Confirmation requires an anonymous visitor; the signup page would otherwise
    # bounce an authenticated user straight to the home page.
    test_client.get("/logout", follow_redirects=True)

    response = test_client.get(
        url_for("confirmemail.confirm_user", token="clearly-not-a-valid-token"), follow_redirects=True
    )

    assert response.request.path == url_for("auth.signup")
