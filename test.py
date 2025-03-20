import smtplib
from email.mime.text import MIMEText

sender_email = "thienan180803@gmail.com"
sender_password = "uxzombrqnspyzwwq"
receiver_email = "an90113@st.vimaru.edu.vn"

msg = MIMEText("Test email")
msg["Subject"] = "Test"
msg["From"] = sender_email
msg["To"] = receiver_email

try:
    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(sender_email, sender_password)
    server.sendmail(sender_email, receiver_email, msg.as_string())
    server.quit()
    print("✅ Email gửi thành công!")
except smtplib.SMTPException as e:
    print(f"❌ Lỗi gửi email: {e}")
