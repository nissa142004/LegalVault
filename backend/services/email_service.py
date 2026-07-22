import logging
import smtplib
from email.message import EmailMessage
from email.utils import formataddr
from pathlib import Path
from threading import Thread

from flask import current_app


logger = logging.getLogger(__name__)
LOGO_PATH = Path(__file__).resolve().parents[2] / "frontend" / "public" / "legalvault-logo.png"


def _send_email(recipient: str, subject: str, heading: str, body: str, action=None) -> bool:
    username = current_app.config.get("MAIL_USERNAME")
    password = current_app.config.get("MAIL_PASSWORD")
    if not username or not password:
        logger.warning("Email not sent because mail credentials are missing.")
        return False

    action_html = ""
    if action:
        label, url = action
        action_html = f'<p style="margin:30px 0"><a href="{url}" style="background:#2dd4bf;color:#06201e;padding:13px 22px;border-radius:10px;text-decoration:none;font-weight:700">{label}</a></p>'
    logo_html = '<img src="cid:legalvault-logo" alt="LegalVault" width="64" style="display:block;margin-bottom:18px">' if LOGO_PATH.exists() else ""
    html = f'''<!doctype html><html><body style="margin:0;background:#f1f5f9;font-family:Arial,sans-serif;color:#172033"><div style="max-width:600px;margin:32px auto;background:#fff;border-radius:16px;padding:38px;border:1px solid #dbe4ea">{logo_html}<div style="font-size:20px;font-weight:800;margin-bottom:28px">LegalVault</div><h1 style="font-size:26px;margin:0 0 14px">{heading}</h1><p style="font-size:15px;line-height:1.7;color:#526174">{body}</p>{action_html}<p style="font-size:12px;color:#94a3b8;margin-top:32px">Secure legal document intelligence, all in one place.</p></div></body></html>'''

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = formataddr((current_app.config["MAIL_FROM_NAME"], username))
    message["To"] = recipient
    message.set_content(f"{heading}\n\n{body}" + (f"\n\n{action[1]}" if action else ""))
    message.add_alternative(html, subtype="html")
    if LOGO_PATH.exists():
        message.get_payload()[1].add_related(LOGO_PATH.read_bytes(), maintype="image", subtype="png", cid="<legalvault-logo>")

    host = current_app.config["MAIL_HOST"]
    port = current_app.config["MAIL_PORT"]

    def deliver():
        try:
            with smtplib.SMTP(host, port, timeout=10) as smtp:
                smtp.starttls()
                smtp.login(username, password)
                smtp.send_message(message)
        except (OSError, smtplib.SMTPException):
            logger.exception("Unable to send email to %s", recipient)

    Thread(target=deliver, name="legalvault-email", daemon=True).start()
    return True


def send_welcome_email(user: dict) -> bool:
    return _send_email(user["email"], "Welcome to LegalVault", f"Welcome, {user['name']}!", "Your secure LegalVault workspace is ready. You can now organize, search, and understand your legal documents with confidence.")


def send_password_reset_email(user: dict, reset_url: str) -> bool:
    return _send_email(user["email"], "Reset your LegalVault password", "Reset your password", "We received a request to reset your LegalVault password. This link expires in one hour. If you did not request this, you can safely ignore this email.", ("Reset password", reset_url))
