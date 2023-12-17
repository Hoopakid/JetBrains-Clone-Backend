from pathlib import Path

from fastapi import FastAPI, APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi.exceptions import HTTPException

from auth.auth import register_router
from auth.utils import verify_token
from database import get_async_session
from models.models import tool, payment_model
from schemes import PaymentModel

app = FastAPI(title='JetBrains', version='1.0.0')
router = APIRouter()


@router.post('/payment_model')
async def create_payment_model(payment: PaymentModel, session: AsyncSession = Depends(get_async_session),
                               token: dict = Depends(verify_token), ):
    user_id = token.get('user_id')

    new_payment = payment_model.insert().values(
        user_id=user_id,
        tool_id=payment.tool_id,
        lifetime=payment.lifetime,
    )

    try:
        await session.execute(new_payment)
        await session.commit()
        return {"message": "Payment model created successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


app.include_router(register_router, prefix='/auth')
app.include_router(router, prefix='/main')
