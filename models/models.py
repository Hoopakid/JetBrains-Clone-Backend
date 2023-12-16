from datetime import datetime

import enum

from sqlalchemy import Table, MetaData, Column, String, Integer, Text, Boolean, Date, ForeignKey, Float, DECIMAL, Enum

from sqlalchemy.dialects.postgresql import ENUM

metadata = MetaData()

class LanguageEnum(enum.Enum):
    uz = 'Uzbek'
    eng = 'English'
    ru = 'Russian'


class RoleEnum(enum.Enum):
    admin = 'Admin'
    user = 'User'


users_data = Table(
    'userdata',
    metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('full_name', String),
    Column('username', String, unique=True),
    Column('email', String, unique=True),
    Column('balance', Float, default=10000.0),
    Column('password', String),
    Column('language', Enum(LanguageEnum)),
    Column('birth_date', Date),
    Column('registered_date', default=datetime.utcnow()),
)

user_role = Table(
    'user_role',
    metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('role_name', Enum(RoleEnum), default='user'),
    Column('user_id', ForeignKey('userdata.id'))
)


class StatusEnum(enum.Enum):
    men = 'Delivered'
    women = 'Processing'
    kids = 'Cancelling'
