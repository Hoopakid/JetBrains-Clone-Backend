import asyncio
from datetime import datetime
import smtplib
from email.message import EmailMessage

from celery import Celery
from fastapi import Depends
from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
from sqlalchemy import update, select
from sqlalchemy.ext.asyncio import AsyncSession

from config import RESET_PASSWORD_REDIRECT_URL, SECRET, REDIS_HOST
from database import get_async_session
from models.models import user_coupon, EndTimeEnum, user_custom_coupon
from config import EnvObjectsForEmail

obj = EnvObjectsForEmail()

celery = Celery(
    "tasks",
    broker=f"redis://{REDIS_HOST}/0",
    backend=f"redis://{REDIS_HOST}/0"
)


def get_mail_conf():
    return ConnectionConfig(
        MAIL_USERNAME=obj.MAIL_USERNAME,
        MAIL_PASSWORD=obj.MAIL_PASSWORD,
        MAIL_FROM=obj.MAIL_FROM,
        MAIL_PORT=obj.MAIL_PORT,
        MAIL_SERVER=obj.MAIL_SERVER,
        MAIL_STARTTLS=False,
        MAIL_SSL_TLS=True,
        USE_CREDENTIALS=True,
        VALIDATE_CERTS=True
    )


@celery.task(bind=True)
def send_mail_task(self, receiver_email: str, coupon: str):
    try:
        mail_config = get_mail_conf()

        fast_mail = FastMail(mail_config)

        message = (
            "Thank you for choosing JetBrains! 🌟 We're thrilled to have you on board "
            "as a proud owner of a new JetBrains coupon. 🛍️\n\n"

            "Your journey with powerful IDEs and development tools is about to get even "
            "more exciting! 🚀 Get ready to boost your productivity and enhance your "
            "coding experience.\n\n"

            "Here's a little sneak peek into what awaits you:\n\n"

            "🚀 Unleash the full potential of JetBrains IDEs.\n"
            "🎨 Customize your coding environment to match your style.\n"
            "🚦 Navigate code effortlessly with smart and intuitive features.\n\n"

            "And now, the moment you've been waiting for... 🎁\n\n"

            "Here is your exclusive JetBrains coupon:\n"
            f"{coupon}\n\n"

            "Feel free to use it during the checkout process and enjoy the incredible "
            "features that JetBrains products have to offer.\n\n"

            "If you have any questions or need assistance, our support team is here "
            "to help! 🤝\n\n"

            "Happy coding! 🚀✨\n\n"

            "\n\n"

            "Best regards,\n"
            "JetBrains Team"
        )

        subject = """🚀 Your JetBrains Coupon Purchase is Complete! 🎉"""

        message_for_email = MessageSchema(
            subject=subject,
            recipients=[receiver_email],
            body=message,
            subtype=MessageType.html
        )
        asyncio.run(fast_mail.send_message(message_for_email))

    except Exception:
        return "Failed"
    return "Sent!"


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


@celery.task(serializer='json')
async def end_coupon_time(session: AsyncSession = Depends(get_async_session)):
    try:
        expired_coupons_query = select(user_coupon).where(
            user_coupon.c.lifetime <= datetime.utcnow,
            user_coupon.c.status == EndTimeEnum.active
        )
        expired_coupons_result = await session.execute(expired_coupons_query)
        expired_coupons = expired_coupons_result.all()

        for coupon in expired_coupons:
            coupon_id = coupon[0]
            update_status_query = (
                update(user_coupon)
                .where(user_coupon.c.id == coupon_id)
                .values(status=EndTimeEnum.expired)
            )
            await session.execute(update_status_query)
        await session.commit()
    except Exception as e:
        print(f'{e}')


@celery.task(serializer='json')
async def end_custom_coupon_time(session: AsyncSession = Depends(get_async_session)):
    try:
        expired_coupons_query = select(user_custom_coupon).where(
            user_custom_coupon.c.lifetime <= datetime.utcnow,
            user_custom_coupon.c.status == EndTimeEnum.active
        )
        expired_coupons_result = await session.execute(expired_coupons_query)
        expired_coupons = expired_coupons_result.all()

        for coupon in expired_coupons:
            coupon_id = coupon[0]
            update_status_query = (
                update(user_custom_coupon)
                .where(user_custom_coupon.c.id == coupon_id)
                .values(status=EndTimeEnum.expired)
            )
            await session.execute(update_status_query)
        await session.commit()
    except Exception as e:
        print(f'{e}')
