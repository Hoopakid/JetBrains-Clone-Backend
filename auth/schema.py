from datetime import datetime, date
from pydantic import BaseModel, EmailStr

from models.models import LanguageEnum


class User(BaseModel):
    full_name: str
    username: str
    email: EmailStr
    balance: float
    password1: str
    password2: str
    language: LanguageEnum
    birth_date: date
    registered_date: datetime


class UserInDB(BaseModel):
    full_name: str
    username: str
    email: str
    balance: float
    password: str
    language: LanguageEnum
    birth_date: date
    registered_date: datetime


class GoogleLogin(BaseModel):
    full_name: str
    username: str
    email: str
    balance: float
    password: str
    language: LanguageEnum
    birth_date: date


class UserInfo(BaseModel):
    full_name: str
    birth_date: date
    username: str
    email: EmailStr


class UserLogin(BaseModel):
    username: str
    password: str
