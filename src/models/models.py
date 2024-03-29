from datetime import datetime

import enum

from sqlalchemy import Table, MetaData, Column, String, Integer, Text, Boolean, Date, ForeignKey, Float, DECIMAL, Enum, \
    TIMESTAMP
from sqlalchemy.orm import relationship

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
    Column('registered_date', TIMESTAMP(timezone=True), nullable=True),
)

user_role = Table(
    'user_role',
    metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('role_name', Enum(RoleEnum), default='user'),
    Column('user_id', ForeignKey('userdata.id'))
)

tools = Table(
    'tools',
    metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('tool_name', String),
    Column('monthly_fee', Float),
    Column('yearly_fee', Float),
)

file = Table(
    'file',
    metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('file', String),
    Column('tool_id', ForeignKey('tools.id')),
    Column('hash', String, unique=True)
)


class LifeTimeEnum(enum.Enum):
    month = 'month'
    year = 'year'


class EndTimeEnum(enum.Enum):
    active = 'active'
    expired = 'expired'


payment_model = Table(
    'payment_model',
    metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('user_id', Integer, ForeignKey('userdata.id'), ),
    Column('tool_id', Integer, ForeignKey('tools.id')),
    Column('lifetime', Enum(LifeTimeEnum)),
    Column('created_at', TIMESTAMP, default=datetime.utcnow),
)


class StatusEnum(enum.Enum):
    delivered = 'Delivered'
    processing = 'Processing'
    cancelling = 'Cancelling'


user_payment = Table(
    'user_payment',
    metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('payment_id', Integer, ForeignKey('payment_model.id')),
    Column('user_id', Integer, ForeignKey('userdata.id')),
    Column('status', Enum(StatusEnum, name='status_enum'), default=StatusEnum.processing),
    Column('created_at', TIMESTAMP, default=datetime.utcnow)
)

user_coupon = Table(
    'coupon',
    metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('coupon', String),
    Column('user_id', Integer, ForeignKey('userdata.id')),
    Column('tool_id', Integer, ForeignKey('tools.id')),
    Column('created_at', TIMESTAMP, default=datetime.utcnow),
    Column('lifetime', TIMESTAMP),
    Column('status', Enum(EndTimeEnum), default=EndTimeEnum.active)
)

user_custom_coupon = Table(
    'custom_coupon',
    metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('user_id', Integer, ForeignKey('userdata.id')),
    Column('phone_number', Integer),
    Column('tool_id', Integer, ForeignKey('tools.id')),
    Column('coupon', String),
    Column('created_at', TIMESTAMP, default=datetime.utcnow),
    Column('lifetime', TIMESTAMP),
    Column('status', Enum(EndTimeEnum), default=EndTimeEnum.active)
)

combo = Table(
    'combo',
    metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('combo_name', String, unique=True),
    Column('monthly_fee', Float, default=0.0),
    Column('yearly_fee', Float, default=0.0),
)

combo_products = Table(
    'combo_products',
    metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('combo_id', Integer, ForeignKey('combo.id')),
    Column('tool_id', Integer, ForeignKey('tools.id')),
)

tool_likes = Table(
    'tool_like',
    metadata,
    Column('id', Integer, primary_key=True),
    Column('user_id', Integer, ForeignKey('userdata.id')),
    Column('tool_id', Integer, ForeignKey('tools.id')),
    Column('time', TIMESTAMP, default=datetime.utcnow),

)


class NumEnum(enum.Enum):
    one = 1,
    two = 2,
    three = 3,
    four = 4,
    five = 5,


tool_comments = Table(
    'tool_comment',
    metadata,
    Column('id', Integer, primary_key=True),
    Column('user_id', Integer, ForeignKey('userdata.id'), unique=True),
    Column('tool_id', Integer, ForeignKey('tools.id')),
    Column('time', TIMESTAMP, default=datetime.utcnow),
    Column('comment', String),
    Column('status', Enum(NumEnum), default=NumEnum.five)
)
