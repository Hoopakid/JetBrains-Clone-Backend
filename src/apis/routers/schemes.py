from typing import Union

from pydantic import BaseModel, Field
from fastapi import UploadFile
from sqlalchemy import Date

from models.models import LifeTimeEnum, tools, NumEnum


class ImageCreate(BaseModel):
    product_id: int
    image: UploadFile


class PaymentModel(BaseModel):
    tool_id: int
    lifetime: LifeTimeEnum


class UserPayment(BaseModel):
    payment_id: int


class ToolCreate(BaseModel):
    tool_name: str
    monthly_fee: float
    yearly_fee: float


class ToolUpdate(BaseModel):
    id: int
    tool_name: str = None
    monthly_fee: float = None
    yearly_fee: float = None


class GetLicenceCustomScheme(BaseModel):
    user_payment_id: int
    tool_id: int
    phone_number: int


class CommentScheme(BaseModel):
    tool_id: int
    content: str
    status: NumEnum
