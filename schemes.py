from pydantic import BaseModel
from fastapi import UploadFile

from models.models import LifeTimeEnum


class ImageCreate(BaseModel):
    product_id: int
    image: UploadFile


class PaymentModel(BaseModel):
    tool_id: int
    lifetime: LifeTimeEnum
