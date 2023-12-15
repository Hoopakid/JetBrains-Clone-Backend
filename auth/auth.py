
from datetime import datetime

from schema import UserInfo, User, UserInDB
from database import get_async_session
from models.models import users_data

from sqlalchemy import select, insert
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends, APIRouter, HTTPException


register_router = APIRouter()
pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')


@register_router.post('/register')
async def register(user: User, session: AsyncSession = Depends(get_async_session)):
    if user.password1 == user.password2:
        if not select(users_data).where(users_data.c.username == user.username).exists:
            raise HTTPException(status_code=400, detail='Username already in use!')
        if not select(users_data).where(users_data.c.email == user.email).exists:
            raise HTTPException(status_code=400, detail='Email already in use!')
        password = pwd_context.hash(user.password1)
        user_in_db = UserInDB(**dict(user), password=password, registered_date=datetime.utcnow())
        query = insert(users_data).values(**dict(user_in_db))
        await session.execute(query)
        await session.commit()
        user_info = UserInfo(**dict(user))
        return dict(user_info)


