import json
import secrets

import redis
import requests

import starlette.status as status
from datetime import datetime

from pydantic import EmailStr

from config import GoogleObjectsForLogin
from tasks.email_tasks.reset_password import send_mail_for_forget_password
from auth.schema import UserInfo, User, UserInDB, UserLogin
from database import get_async_session

from sqlalchemy import select, insert, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import NoResultFound
from fastapi import Depends, APIRouter, HTTPException
from dotenv import load_dotenv
from passlib.context import CryptContext
from utils.auth_utils import verify_token, generate_token
from models.models import users_data, LanguageEnum

from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
redis_client = redis.StrictRedis(host='redis', port=6379, db=0, decode_responses=True)

obj = GoogleObjectsForLogin

load_dotenv()
register_router = APIRouter()

pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')


@register_router.get("/login/google")
async def login_google():
    return {
        "url": f"https://accounts.google.com/o/oauth2/auth?response_type=code&client_id={obj.client_id}&redirect_uri={obj.redirect_url}&scope=openid%20profile%20email&access_type=offline"
    }


@register_router.get("/auth/google")
async def auth_google(code: str, session: AsyncSession = Depends(get_async_session)):
    token_url = "https://accounts.google.com/o/oauth2/token"
    data = {
        "code": code,
        "client_id": obj.client_id,
        "client_secret": obj.client_secret,
        "redirect_uri": obj.redirect_url,
        "grant_type": "authorization_code",
    }
    response = requests.post(token_url, data=data)
    access_token = response.json().get("access_token")
    user_info_data = requests.get("https://www.googleapis.com/oauth2/v1/userinfo",
                                  headers={"Authorization": f"Bearer {access_token}"})
    birth_date = datetime.strptime('2008-07-14', "%Y-%m-%d").date()
    user_data = {
        'full_name': user_info_data.json().get('name'),
        'username': user_info_data.json().get('email'),
        'email': user_info_data.json().get('email'),
        'balance': 10000.0,
        'password': pwd_context.hash(user_info_data.json().get('email')),
        'language': LanguageEnum.uz,
        'birth_date': birth_date
    }

    user_exist_query = select(users_data).where(users_data.c.username == user_info_data.json().get('email'))
    user_exist_data = await session.execute(user_exist_query)
    try:
        result = user_exist_data.scalars().one()
    except NoResultFound:
        try:
            query = insert(users_data).values(**user_data)
            await session.execute(query)

            user_data = await session.execute(
                select(users_data).where(users_data.c.username == user_info_data.json().get('email')))
            user_data = user_data.one()

            token = generate_token(user_data.id)
            await session.commit()
            return token
        except Exception as e:
            raise HTTPException(detail=f'{e}', status_code=status.HTTP_400_BAD_REQUEST)
    finally:
        await session.close()


@register_router.post('/register')
async def register(user: User, session: AsyncSession = Depends(get_async_session)):
    try:
        if user.password1 == user.password2:
            if not select(users_data).where(users_data.c.username == user.username).exists:
                return {'success': False, 'message': 'Username already exists!'}
            if not select(users_data).where(users_data.c.email == user.email).exists:
                return {'success': False, 'message': 'Email already exists!'}
            password = pwd_context.hash(user.password1)
            user_in_db = UserInDB(**dict(user), password=password, joined_at=datetime.utcnow())
            query = insert(users_data).values(**dict(user_in_db))
            await session.execute(query)
            await session.commit()
            info_user = UserInfo(**dict(user_in_db))
            return dict(info_user)
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))


@register_router.post('/login')
async def login(user: UserLogin, session: AsyncSession = Depends(get_async_session)):
    query = select(users_data).where(users_data.c.username == user.username)
    userdata = await session.execute(query)
    user_data = userdata.one()
    if pwd_context.verify(user.password, user_data.password):
        token = generate_token(user_data.id)
        return token
    else:
        return {'success': False, 'message': 'Username or password is not correct!'}


@register_router.get('/user-info', response_model=UserInfo)
async def user_info(token: dict = Depends(verify_token), session: AsyncSession = Depends(get_async_session)):
    if token is None:
        raise HTTPException(status_code=401, detail='Token not provided!')

    user_id = token.get('user_id')

    query = select(users_data).where(users_data.c.id == user_id)
    user = await session.execute(query)
    try:
        result = user.one()
        return result
    except NoResultFound:
        raise HTTPException(status_code=404, detail='User not found!')


@register_router.get('/forget-password/{email}')
async def forget_password(
        email: EmailStr,
        session: AsyncSession = Depends(get_async_session)
):
    try:
        user = select(users_data).where(users_data.c.email == email)
        user_data = await session.execute(user)
        if user_data.fetchone() is None:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail="Invalid Email address")
        token = secrets.token_urlsafe(32)

        redis_client.set(f'{token}', json.dumps({'email': email}))
        send_mail_for_forget_password(email, token)
        return {"detail": "Check your email"}
    except Exception as e:
        raise HTTPException(detail=f'{e}', status_code=status.HTTP_400_BAD_REQUEST)


@register_router.post('/reset-password/{token}')
async def reset_password(
        token: str,
        new_password: str,
        confirm_password: str,
        session: AsyncSession = Depends(get_async_session)
):
    try:
        if new_password != confirm_password:
            raise HTTPException(detail="Passwords are not same!!!", status_code=status.HTTP_400_BAD_REQUEST)
        user_data_json = redis_client.get(token)
        if user_data_json is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired token")

        user_data = json.loads(user_data_json)
        email = user_data.get('email')

        update_password = update(users_data).where(users_data.c.email == email).values(
            password=pwd_context.hash(new_password))
        await session.execute(update_password)
        await session.commit()

        redis_client.delete(token)

        return {"detail": "Password reset successfully"}
    except Exception as e:
        raise HTTPException(detail=f'{e}', status_code=status.HTTP_400_BAD_REQUEST)
