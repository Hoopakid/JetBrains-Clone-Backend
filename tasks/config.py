from celery import Celery
from fastapi_mail import ConnectionConfig

from config import REDIS_HOST
from tasks.email_tasks.reset_password import obj

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
