from unittest.mock import MagicMock

import pytest
from flask import Flask

from app.features.mail.services import MailService

pytestmark = pytest.mark.unit


def _service_with_mock_mail():
    service = MailService()
    service.mail = MagicMock()
    service.sender = "noreply@example.com"
    return service


def test_send_email_builds_and_sends_the_message():
    service = _service_with_mock_mail()

    service.send_email("Subject", ["to@example.com"], "Body", html_body="<b>Body</b>")

    service.mail.send.assert_called_once()
    message = service.mail.send.call_args.args[0]
    assert message.subject == "Subject"
    assert message.recipients == ["to@example.com"]
    assert message.body == "Body"
    assert message.html == "<b>Body</b>"


def test_send_email_attaches_files():
    service = _service_with_mock_mail()

    service.send_email("S", ["to@example.com"], "B", attachments=[("report.pdf", b"data")])

    message = service.mail.send.call_args.args[0]
    assert len(message.attachments) == 1


def test_init_app_populates_mail_configuration():
    app = Flask(__name__)

    MailService().init_app(app)

    assert isinstance(app.config["MAIL_PORT"], int)
    assert app.config["MAIL_USE_TLS"] in (True, False)
    assert app.config["MAIL_SERVER"]
    assert app.config["MAIL_DEFAULT_SENDER"]
