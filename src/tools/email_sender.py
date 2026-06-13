import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, ReplyTo
from dotenv import load_dotenv

load_dotenv()

SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
FROM_EMAIL = os.getenv("FROM_EMAIL")
REPLY_TO_EMAIL = os.getenv("REPLY_TO_EMAIL")


def send_email(to_email: str, subject: str, body: str) -> bool:
    message = Mail(
        from_email=FROM_EMAIL,
        to_emails=to_email,
        subject=subject,
        plain_text_content=body
    )
    if REPLY_TO_EMAIL:
        message.reply_to = ReplyTo(REPLY_TO_EMAIL)

    sg = SendGridAPIClient(SENDGRID_API_KEY)
    response = sg.send(message)

    success = response.status_code in (200, 202)
    if success:
        print(f"[email] Gönderildi → {to_email} (status: {response.status_code})")
    else:
        print(f"[email] HATA → status: {response.status_code}, body: {response.body}")

    return success
