from __future__ import annotations

import smtplib
import ssl
from email.message import EmailMessage

from relay_probe.config import Settings

settings = Settings()


def smtp_configured() -> bool:
    return bool(
        settings.smtp_host.strip()
        and settings.smtp_from.strip()
    )


def send_reset_email(to_addr: str, subject: str, body_text: str, body_html: str) -> None:
    if not smtp_configured():
        raise RuntimeError("SMTP not configured")

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = settings.smtp_from.strip()
    msg["To"] = to_addr.strip()
    msg.set_content(body_text)
    msg.add_alternative(body_html, subtype="html")

    timeout = float(settings.smtp_timeout_sec)
    context = ssl.create_default_context()
    if settings.smtp_use_ssl:
        with smtplib.SMTP_SSL(
            settings.smtp_host,
            settings.smtp_port,
            timeout=timeout,
            context=context,
        ) as client:
            if settings.smtp_username:
                client.login(settings.smtp_username, settings.smtp_password)
            client.send_message(msg)
            return

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=timeout) as client:
        if settings.smtp_use_tls:
            client.starttls(context=context)
        if settings.smtp_username:
            client.login(settings.smtp_username, settings.smtp_password)
        client.send_message(msg)
