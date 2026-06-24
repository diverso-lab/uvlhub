from unittest.mock import MagicMock, call, patch

import pytest

from app.features.webhook.services import DEPLOY_COMMANDS, WebhookService

pytestmark = pytest.mark.service


def test_deploy_updates_and_restarts_both_containers():
    service = WebhookService()
    worker, web = MagicMock(name="worker"), MagicMock(name="web")

    with (
        patch.object(service, "get_worker_container", return_value=worker),
        patch.object(service, "get_web_container", return_value=web),
        patch.object(service, "execute_container_command") as run,
        patch.object(service, "log_deployment") as log_deployment,
        patch.object(service, "restart_container") as restart,
    ):
        service.deploy()

    # Every deploy command runs against both containers.
    expected = [call(worker, cmd) for cmd in DEPLOY_COMMANDS] + [call(web, cmd) for cmd in DEPLOY_COMMANDS]
    run.assert_has_calls(expected, any_order=False)
    assert log_deployment.call_count == 2
    assert restart.call_count == 2
