import pytest

pytestmark = pytest.mark.integration


def test_deploy_rejects_a_request_without_authorization(test_client):
    assert test_client.post("/webhook/deploy").status_code == 403


def test_deploy_rejects_a_wrong_token(test_client):
    response = test_client.post("/webhook/deploy", headers={"Authorization": "Bearer wrong"})

    assert response.status_code == 403
