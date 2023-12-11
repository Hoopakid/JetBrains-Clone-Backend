from datetime import datetime

from sqlalchemy import Table, MetaData, Column, String, Integer, Text, Boolean, Date, ForeignKey, Float, DECIMAL, Enum

metadata = MetaData()


class LanguageEnum(Enum):
    English = 'English'
    Uzbek = 'Uzbek'
    Russian = 'Russian'


class RoleEnum(Enum):
    admin = 'admin'
    user = 'user'


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
    Column('role_name', Enum(RoleEnum), default=RoleEnum.user),
    Column('user_id', ForeignKey('userdata.id'))
)

tools = Table(
    'tools',
    metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('tool_name', String),
    Column('tool_description', Text),
    Column('annual_fee', DECIMAL(precision=10, scale=2)),
    Column('monthly_fee', DECIMAL(precision=10, scale=2)),
)

licences = Table(
    'licences',
    metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('tool_id', ForeignKey('tools.id')),
    Column('user_id', ForeignKey('userdata.id')),
    Column('email', String),
    Column('created_at', Date)
)

user_payment_model = Table(
    'user_payment',
    metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('licence_id', ForeignKey('licences.id')),
    Column('user_id', ForeignKey('licences.user_id')),
    Column('street_address', String),
    Column('city', String),
    Column('email', String),
    Column('lifetime', ForeignKey('tools.id')),
    Column('cost', ForeignKey('tools.id')),
)


class StatusEnum(Enum):
    delivered = 'Delivered',
    processing = 'Processing',
    cancelled = 'Cancelled'


user_payment_status = Table(
    'user_payment_status',
    metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('payment_id', ForeignKey('user_payment.id')),
    Column('payment_status', Enum(StatusEnum)),
    Column('user_id', ForeignKey('user_payment.user_id'))
)

coupon = Table(
    'coupon',
    metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('coupon', String),
    Column('lifetime', ForeignKey('user_payment.lifetime')),
    Column('end_time', Date),
    Column('user_id', ForeignKey('user_payment.user_id'))
)

custom_coupon = Table(
    'custom_coupon',
    metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('user_id', ForeignKey('user_payment.user_id')),
    Column('first_name', String),
    Column('last_name', String),
    Column('coupon', ForeignKey('coupon.coupon')),
    Column('phone_number', ForeignKey('phone_number'))
)
