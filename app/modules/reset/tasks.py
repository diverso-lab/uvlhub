from app import mail_service


def send_reset_password_email(email: str, link: str):
    """Send password reset email asynchronously."""
    subject = "Password Reset Request"
    body = (
        f"Hello,\n\n"
        f"To reset your password, click the link below:\n\n{link}\n\n"
        f"This link will expire in 1 hour.\n\n"
        f"If you didn’t request this, please ignore this message."
    )

    try:
        mail_service.send_email(subject, [email], body)
        print(f"[MAIL] ✅ Password reset email sent to {email}")
    except Exception as e:
        print(f"[MAIL] ❌ Failed to send reset email to {email}: {e}")


def send_reset_confirmation_email(email: str):
    """Envía el correo confirmando que la contraseña ha sido restablecida."""
    try:
        subject = "Your Password Has Been Reset"
        body = (
            "Your password has been successfully updated. If you did not do this, please contact support immediately."
        )
        mail_service.send_email(subject, [email], body)
        print(f"[MAIL] ✅ Reset confirmation email sent to {email}")
    except Exception as e:
        print(f"[MAIL] ❌ Failed to send reset confirmation email to {email}: {e}")
