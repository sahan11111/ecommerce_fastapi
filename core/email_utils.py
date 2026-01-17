from email.message import EmailMessage
import smtplib
import os
from dotenv import load_dotenv

load_dotenv()
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD" )  # ⚠️ use env variable in prod

def send_otp_email(to_email: str, username: str, otp: str):
    msg = EmailMessage()
    msg["Subject"] = "Verify your account (OTP)"
    msg["From"] = EMAIL_HOST_USER
    msg["To"] = to_email

    msg.set_content(
        f"""
Hi {username},

Your OTP for account verification is:

🔐 {otp}

This OTP is valid for 10 minutes.

If you did not request this, ignore this email.

Thanks,
Team 🚀
"""
    )

    with smtplib.SMTP(EMAIL_HOST, EMAIL_PORT) as server:
        server.starttls()
        server.login(EMAIL_HOST_USER, EMAIL_HOST_PASSWORD)
        server.send_message(msg)

