# utils/email_service.py
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_email(to, subject, body, from_email="noreply@example.com", smtp_server="smtp.example.com", smtp_port=587, username="", password=""):
    """
    Sends a simple email using SMTP.
    """
    msg = MIMEMultipart()
    msg["From"] = from_email
    msg["To"] = to
    msg["Subject"] = subject

    msg.attach(MIMEText(body, "html"))  # HTML body

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            if username and password:
                server.login(username, password)
            server.sendmail(from_email, to, msg.as_string())
        print(f"Email sent to {to}")
    except Exception as e:
        print(f"Failed to send email to {to}: {e}")
