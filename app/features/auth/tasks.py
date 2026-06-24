import logging

from app import create_app
from app.features.confirmemail.services import ConfirmemailService

confirmemail_service = ConfirmemailService()

logger = logging.getLogger(__name__)
app = create_app()


def send_confirmation_email(email: str):
    """Asynchronous task to send the confirmation email."""
    logger.info(f"[EMAIL] Sending confirmation email to {email}")

    with app.app_context():
        try:
            confirmemail_service.send_confirmation_email(email)
            logger.info(f"[EMAIL] Confirmation email sent to {email}")
        except Exception as e:
            logger.exception(f"[EMAIL] Error sending email to {email}: {e}")
