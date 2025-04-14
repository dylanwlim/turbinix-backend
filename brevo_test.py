import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv
import os

load_dotenv()

msg = EmailMessage()
msg['Subject'] = "Test Email from Turbinix"
msg['From'] = "Turbinix Verification <no-reply@turbinix.one>"
msg['To'] = "<your-email@gmail.com>"  # <-- replace with your real address
msg.set_content("This is a test email from the Turbinix backend system.")

try:
    with smtplib.SMTP(os.getenv("SMTP_SERVER"), int(os.getenv("SMTP_PORT", 587))) as server:
        server.starttls()
        server.login(os.getenv("SMTP_USER"), os.getenv("SMTP_PASS"))
        server.send_message(msg)
        print("✅ Test email sent.")
except Exception as e:
    print("❌ Error sending test email:", repr(e))
