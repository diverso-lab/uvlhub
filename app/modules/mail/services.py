import os

from flask_mail import Mail, Message

from app.modules.mail.repositories import MailRepository
from core.services.BaseService import BaseService


class MailService(BaseService):

    def __init__(self):
        super().__init__(MailRepository())
        self.mail = None
        self.sender = None

    def init_app(self, app):
        app.config["MAIL_SERVER"] = os.getenv("MAIL_SERVER", "smtp.office365.com")
        app.config["MAIL_PORT"] = int(os.getenv("MAIL_PORT", "587"))
        app.config["MAIL_USE_TLS"] = os.getenv("MAIL_USE_TLS", "True") == "True"
        app.config["MAIL_USE_SSL"] = os.getenv("MAIL_USE_SSL", "False") == "True"
        app.config["MAIL_USERNAME"] = os.getenv("MAIL_USERNAME", "tu_correo@tudominio.com")
        app.config["MAIL_PASSWORD"] = os.getenv("MAIL_PASSWORD", "tu_password")
        app.config["MAIL_DEFAULT_SENDER"] = os.getenv("MAIL_USERNAME")

        self.mail = Mail(app)
        self.sender = app.config["MAIL_USERNAME"]

    def send_email(self, subject, recipients, body, html_body=None):
        msg = Message(subject, sender=self.sender, recipients=recipients)
        msg.body = body
        if html_body:
            msg.html = html_body

        self.mail.send(msg)
