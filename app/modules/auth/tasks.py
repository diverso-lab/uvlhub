import logging

from app import create_app
from app.modules.confirmemail.services import ConfirmemailService

confirmemail_service = ConfirmemailService()

logger = logging.getLogger(__name__)
app = create_app()


def send_confirmation_email(email: str):
    """Tarea asíncrona para enviar el correo de confirmación."""
    logger.info(f"[EMAIL] Enviando correo de confirmación a {email}")

    with app.app_context():
        try:
            confirmemail_service.send_confirmation_email(email)
            logger.info(f"[EMAIL] ✅ Correo de confirmación enviado a {email}")
        except Exception as e:
            logger.exception(f"[EMAIL] ❌ Error enviando correo a {email}: {e}")
