import pytest

pytestmark = pytest.mark.integration


def test_orcid_login_issues_a_redirect(test_client):
    test_client.get("/logout", follow_redirects=True)

    response = test_client.get("/orcid/login")

    assert response.status_code == 302
