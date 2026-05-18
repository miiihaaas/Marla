"""PR Marla Beograd — Flask backend za kontakt formu.

Servira statički sajt i pruža /api/contact endpoint koji prima JSON
i šalje email primaocu definisanom u MAIL_TO env varijabli.
"""

from __future__ import annotations

import os
import re
import sys
import smtplib
import ssl
from datetime import datetime
from email.message import EmailMessage
from email.utils import formataddr
from html import escape
from pathlib import Path
from zoneinfo import ZoneInfo

from flask import Flask, jsonify, request, send_from_directory

# Učitaj .env ako postoji (lokalni dev); u produkciji (cPanel) env varijable
# se postavljaju kroz panel i .env fajl ne mora postojati.
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

BASE_DIR = Path(__file__).resolve().parent

app = Flask(
    __name__,
    static_folder=str(BASE_DIR / "static"),
    static_url_path="/static",
)

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
BELGRADE_TZ = ZoneInfo("Europe/Belgrade")

MESSAGE_MIN = 10
MESSAGE_MAX = 5000
NAME_MAX = 200
EMAIL_MAX = 320
PHONE_MAX = 50


def env(key: str, default: str = "") -> str:
    return os.environ.get(key, default).strip()


def validate(payload: dict) -> tuple[dict | None, str | None]:
    if not isinstance(payload, dict):
        return None, "Neispravan format zahteva."

    name = (payload.get("name") or "").strip()
    email_addr = (payload.get("email") or "").strip()
    phone = (payload.get("phone") or "").strip()
    message = (payload.get("message") or "").strip()

    if not name:
        return None, "Molimo unesite ime."
    if len(name) > NAME_MAX:
        return None, "Ime je predugačko."

    if not email_addr:
        return None, "Molimo unesite email."
    if len(email_addr) > EMAIL_MAX or not EMAIL_REGEX.match(email_addr):
        return None, "Email nije ispravan."

    if len(phone) > PHONE_MAX:
        return None, "Telefon je predugačak."

    if not message:
        return None, "Molimo unesite poruku."
    if len(message) < MESSAGE_MIN:
        return None, f"Poruka je prekratka (minimum {MESSAGE_MIN} karaktera)."
    if len(message) > MESSAGE_MAX:
        return None, f"Poruka je predugačka (maksimum {MESSAGE_MAX} karaktera)."

    return {"name": name, "email": email_addr, "phone": phone, "message": message}, None


def build_email(data: dict) -> EmailMessage:
    mail_from = env("MAIL_FROM")
    mail_to = env("MAIL_TO")

    timestamp = datetime.now(BELGRADE_TZ).strftime("%d.%m.%Y. %H:%M")

    msg = EmailMessage()
    msg["Subject"] = f"Nova poruka sa sajta — {data['name']}"
    msg["From"] = formataddr(("PR Marla Sajt", mail_from))
    msg["To"] = mail_to
    msg["Reply-To"] = data["email"]

    phone_row = (
        f"<tr><td style='padding:6px 12px;color:#7d8aa0;'>Telefon</td>"
        f"<td style='padding:6px 12px;color:#0f1a30;'>{escape(data['phone'])}</td></tr>"
        if data["phone"] else ""
    )

    html_body = f"""\
<!doctype html>
<html><body style="font-family:Arial,Helvetica,sans-serif;background:#f4f6fa;padding:24px;color:#0f1a30;">
  <div style="max-width:600px;margin:0 auto;background:#ffffff;border-radius:8px;padding:28px;border:1px solid #e2e8f0;">
    <h2 style="font-family:Georgia,serif;color:#1a2540;margin:0 0 6px;">Nova poruka sa sajta</h2>
    <p style="color:#7d8aa0;margin:0 0 22px;font-size:13px;">PR Marla Beograd · {escape(timestamp)} (Europe/Belgrade)</p>

    <table style="width:100%;border-collapse:collapse;font-size:14px;margin-bottom:20px;">
      <tr><td style="padding:6px 12px;color:#7d8aa0;width:120px;">Ime</td>
          <td style="padding:6px 12px;color:#0f1a30;">{escape(data['name'])}</td></tr>
      <tr><td style="padding:6px 12px;color:#7d8aa0;">Email</td>
          <td style="padding:6px 12px;color:#0f1a30;"><a href="mailto:{escape(data['email'])}" style="color:#1a2540;">{escape(data['email'])}</a></td></tr>
      {phone_row}
    </table>

    <div style="border-top:1px solid #e2e8f0;padding-top:18px;">
      <div style="color:#7d8aa0;font-size:13px;margin-bottom:8px;">Poruka</div>
      <div style="white-space:pre-wrap;line-height:1.55;color:#0f1a30;">{escape(data['message'])}</div>
    </div>
  </div>
</body></html>
"""

    plain_body = (
        f"Nova poruka sa sajta — PR Marla Beograd\n"
        f"{timestamp} (Europe/Belgrade)\n\n"
        f"Ime: {data['name']}\n"
        f"Email: {data['email']}\n"
        + (f"Telefon: {data['phone']}\n" if data['phone'] else "")
        + f"\nPoruka:\n{data['message']}\n"
    )

    msg.set_content(plain_body)
    msg.add_alternative(html_body, subtype="html")
    return msg


def send_email(msg: EmailMessage) -> None:
    host = env("SMTP_HOST")
    port = int(env("SMTP_PORT", "465"))
    user = env("SMTP_USER")
    password = env("SMTP_PASS")

    if not (host and user and password and env("MAIL_FROM") and env("MAIL_TO")):
        raise RuntimeError("SMTP konfiguracija nije kompletna (proveri .env / cPanel env varijable).")

    context = ssl.create_default_context()
    if env("SMTP_INSECURE_TLS").lower() == "true":
        # Shared cPanel/a2 hosting cert chains often nisu RFC 5280 strict-compliant.
        # Python 3.13+ ih odbija po defaultu — ovaj flag opušta samo strict X509 mod
        # (konekcija i dalje TLS-enkriptovana, cert se i dalje verifikuje).
        context.verify_flags &= ~ssl.VERIFY_X509_STRICT

    # Port 465 = implicit SSL (SMTP_SSL). Port 587 = plain + STARTTLS. Port 25 = plain.
    if port == 465:
        smtp = smtplib.SMTP_SSL(host, port, context=context, timeout=30)
    else:
        smtp = smtplib.SMTP(host, port, timeout=30)
        if port == 587:
            smtp.starttls(context=context)

    try:
        smtp.login(user, password)
        smtp.send_message(msg)
    finally:
        smtp.quit()


@app.route("/")
def index():
    return send_from_directory(str(BASE_DIR), "index.html")


# Rate limiting bi išao ovde — npr. flask-limiter sa @limiter.limit("5/minute")
# da spreči zloupotrebu /api/contact endpoint-a. Out of scope za prvu iteraciju.
@app.route("/api/contact", methods=["POST"])
def contact():
    payload = request.get_json(silent=True) or {}
    data, error = validate(payload)
    if error:
        return jsonify(ok=False, error=error), 400

    try:
        msg = build_email(data)
        send_email(msg)
    except Exception as exc:
        print(f"[contact] SMTP error: {exc!r}", file=sys.stderr)
        return jsonify(ok=False, error="Greška pri slanju, pokušajte ponovo."), 500

    return jsonify(ok=True), 200


if __name__ == "__main__":
    debug = env("FLASK_ENV") != "production"
    app.run(host="127.0.0.1", port=5000, debug=debug)
