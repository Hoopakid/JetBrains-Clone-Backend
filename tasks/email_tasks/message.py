import asyncio

from fastapi_mail import FastMail, MessageSchema, MessageType

from tasks.config import celery, get_mail_conf


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
