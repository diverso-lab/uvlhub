import os
import smtplib

import click


@click.command("mail:test", help="Tests SMTP connection using environment variables.")
def mail_test():
    host = os.getenv("MAIL_SERVER", "localhost")
    port = int(os.getenv("MAIL_PORT", 587))
    user = os.getenv("MAIL_USERNAME")
    password = os.getenv("MAIL_PASSWORD")
    use_tls = os.getenv("MAIL_USE_TLS", "true").lower() == "true"
    use_ssl = os.getenv("MAIL_USE_SSL", "false").lower() == "true"

    click.echo(click.style(f"🔍 Testing SMTP connection to {host}:{port}...", fg="cyan"))

    try:
        if use_ssl:
            server = smtplib.SMTP_SSL(host, port, timeout=10)
        else:
            server = smtplib.SMTP(host, port, timeout=10)
            if use_tls:
                server.starttls()

        if user and password:
            server.login(user, password)

        server.noop()  # simple ping
        click.echo(click.style("✅ SMTP connection successful!", fg="green"))

    except Exception as e:
        click.echo(click.style(f"❌ SMTP connection failed: {e}", fg="red"))

    finally:
        try:
            server.quit()
        except Exception:
            pass
