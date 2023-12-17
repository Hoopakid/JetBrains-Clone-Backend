from datetime import datetime

from .schema import UserInfo, User, UserInDB, UserLogin
from database import get_async_session

from sqlalchemy import select, insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import NoResultFound
from fastapi import Depends, APIRouter, HTTPException
from dotenv import load_dotenv
from passlib.context import CryptContext

from .utils import verify_token, generate_token
from models.models import users_data

load_dotenv()
register_router = APIRouter()

pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')


@register_router.post('/register')
async def register(user: User, session: AsyncSession = Depends(get_async_session)):
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
        user_info = UserInfo(**dict(user_in_db))
        return dict(user_info)


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
