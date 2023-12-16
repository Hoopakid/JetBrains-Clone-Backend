from datetime import datetime, date
from pydantic import BaseModel


class User(BaseModel):
    full_name: str
    username: str
    email: str
    balance: float
    password1: str
    password2: str
    language: str
    birth_date: date
    registered_date: datetime


class UserInDB(BaseModel):
    full_name: str
    username: str
    email: str
    balance: float
    password: str
    language: str
    birth_date: date
    registered_date: datetime


class UserInfo(BaseModel):
    full_name: str
    username: str
    email: str
    birth_date: date


class UserLogin(BaseModel):
    username: str
    password: str
