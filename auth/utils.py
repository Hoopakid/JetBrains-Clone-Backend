import os
import jwt
import secrets
from datetime import datetime, timedelta
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import Depends, HTTPException
from dotenv import load_dotenv

load_dotenv()
secret_key = os.environ.get('SECRET')
algorithm = 'HS256'
security = HTTPBearer()


def generate_token(user_id: int):
    jti_access = str(secrets.token_urlsafe(32))
    jti_refresh = str(secrets.token_urlsafe(32))
    data_access_token = {
        'token_type': 'access',
        'exp': datetime.utcnow() + timedelta(minutes=30),
        'user_id': user_id,
        'jti': jti_access
    }
    data_refresh_token = {
        'token_type': 'refresh',
        'exp': datetime.utcnow() + timedelta(days=1),
        'user_id': user_id,
        'jti': jti_refresh
    }
    access_token = jwt.encode(data_access_token, secret_key, algorithm)
    refresh_token = jwt.encode(data_refresh_token, secret_key, algorithm)

    return {
        'access_token': access_token,
        'refresh_token': refresh_token
    }


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        token = credentials.credentials
        secret_key = os.environ.get('SECRET')

        payload = jwt.decode(token, secret_key, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
