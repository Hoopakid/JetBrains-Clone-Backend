import smtplib
from email.message import EmailMessage

from config import EnvObjectsForEmail, RESET_PASSWORD_REDIRECT_URL, SECRET, RESET_PASSWORD_EXPIRY_MINUTES
from tasks.config import celery

obj = EnvObjectsForEmail


def get_email_objects(user_email, token):
    email = EmailMessage()
    email['Subject'] = f'Verify email'
    email['From'] = obj.MAIL_USERNAME
    email['To'] = user_email

    forget_url_link = f"{RESET_PASSWORD_REDIRECT_URL}/{SECRET}"

    email.set_content(
        f"""
            <html>
            <body>
                <p>
                    Hello, 😊<br><br>
                    You have requested to reset your password for <b>JetBrains</b>.<br>
                    Please click on the following link within {RESET_PASSWORD_EXPIRY_MINUTES} minutes to reset your password:<br>
                    <a href="{forget_url_link}">{forget_url_link}</a><br><br>
                    Your token {token} <br>
                    If you did not request this reset, please ignore this email. 🙅‍♂️<br><br>
                    Regards, <br>
                    JetBrains Team 🚀
                </p>
            </body>
            </html>
        """,
        subtype='html',
    )
    return email


@celery.task
def send_mail_for_forget_password(email: str, token: str):
    email = get_email_objects(email, token)
    with smtplib.SMTP_SSL(obj.MAIL_SERVER, obj.MAIL_PORT) as server:
        server.login(obj.MAIL_USERNAME, obj.MAIL_PASSWORD)
        server.send_message(email)
