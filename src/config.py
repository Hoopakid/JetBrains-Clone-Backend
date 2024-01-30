import os
from dotenv import load_dotenv

load_dotenv()

DB_NAME = os.environ.get('POSTGRES_DB')
DB_USER = os.environ.get('POSTGRES_USER')
DB_PASSWORD = os.environ.get('POSTGRES_PASSWORD')
DB_HOST = os.environ.get('POSTGRES_HOST')
DB_PORT = os.environ.get('POSTGRES_PORT')
SECRET = os.environ.get('SECRET')

REDIS_HOST = os.getenv('REDIS_HOST')

RESET_PASSWORD_REDIRECT_URL = os.getenv('RESET_PASSWORD_REDIRECT_URL')
RESET_PASSWORD_EXPIRY_MINUTES = os.getenv('EXPIRY_MINUTES')


class EnvObjectsForEmail:
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    MAIL_FROM = os.getenv('MAIL_FROM')
    MAIL_PORT = os.getenv('MAIL_PORT')
    MAIL_SERVER = os.getenv('MAIL_SERVER')


class GoogleObjectsForLogin:
    client_id = os.getenv('GOOGLE_CLIENT_ID')
    client_secret = os.getenv('GOOGLE_CLIENT_SECRET_KEY')
    redirect_url = os.getenv('GOOGLE_REDIRECT_URL')
