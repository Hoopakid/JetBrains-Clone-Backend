import secrets
import aiofiles
import starlette.status as status

from pathlib import Path

from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert, update
from sqlalchemy.sql import exists
from sqlalchemy.exc import NoResultFound

from fastapi import FastAPI, APIRouter, Depends, UploadFile
from fastapi.exceptions import HTTPException

from auth.auth import register_router
from auth.utils import verify_token
from database import get_async_session
from models.models import tools, payment_model, LifeTimeEnum, users_data, user_role, file, tools, user_payment, \
    StatusEnum
from schemes import PaymentModel, UserPayment
from utils import generate_coupon

app = FastAPI(title='JetBrains', version='1.0.0')
router = APIRouter()


@router.post('/payment_model')
async def create_payment_model(
        payment: PaymentModel,
        session: AsyncSession = Depends(get_async_session),
        token: dict = Depends(verify_token),
):
    if token is None:
        raise HTTPException(status_code=401, detail='Token not provided!')

    user_id = token.get('user_id')

    new_payment = insert(payment_model).values(
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


@router.post('/payment/{payment_id}')
async def payment_user(
        payment_id: int,
        session: AsyncSession = Depends(get_async_session),
        token: dict = Depends(verify_token)
):
    try:
        user_id = token.get('user_id')

        if_payment_query = select(user_payment).where(
            (user_payment.c.payment_id == payment_id) & (user_payment.c.user_id == user_id)
        )
        if_payment = await session.execute(if_payment_query)
        if if_payment:
            raise HTTPException(status_code=status.HTTP_204_NO_CONTENT, detail='Already in active')

        payment_query = select(payment_model).join(users_data).where(
            (payment_model.c.id == payment_id) & (users_data.c.id == user_id)
        )
        payment_result = await session.execute(payment_query)
        payment = payment_result.one()
        if not payment:
            raise HTTPException(status_code=404, detail="Payment not found!")

        month_or_year = str(payment[3])[13:]

        tool_id = payment[2]
        tool_query = select(tools).where(tools.c.id == tool_id)
        tool__result = await session.execute(tool_query)
        tool_result = tool__result.one()

        if month_or_year == 'month':
            paid_amount = tool_result[2]
        elif month_or_year == 'year':
            paid_amount = tool_result[3]
        else:
            raise HTTPException(detail='Invalid designation', status_code=status.HTTP_404_NOT_FOUND)

        user__balance = await session.execute(select(users_data).where(users_data.c.id == user_id))
        user_balance = user__balance.one()[4]
        if user_balance < paid_amount:
            raise HTTPException(detail='Insufficient funds in your account', status_code=status.HTTP_400_BAD_REQUEST)

        user_new_balance = user_balance - paid_amount
        user_balance_update_query = update(users_data).where(users_data.c.id == user_id).values(
            balance=user_new_balance
        )
        await session.execute(user_balance_update_query)

        insert_query = insert(user_payment).values(
            payment_id=payment_id,
            user_id=user_id,
        )

        await session.execute(insert_query)

        await session.commit()
        return {"status": status.HTTP_201_CREATED, "detail": "Your payment is now active!"}

    except HTTPException as e:
        return e

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get('/get-licence-code')
async def get_licence_code(
        session: AsyncSession = Depends(get_async_session),
        token: dict = Depends(verify_token)
):
    try:
        user_id = token.get('user_id')

        if_payment_query = select(user_payment).where(
            user_payment.c.user_id == user_id
        )
        if_payment = await session.execute(if_payment_query)
        if not if_payment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Unauthorized')
        coupon = generate_coupon(user_id)

        return {"status": status.HTTP_200_OK, "coupon": coupon}
    except Exception as e:
        raise HTTPException(detail=f'{e}')


@router.post('/upload-file')
async def upload_file(
        file_upload: UploadFile,
        tool_id: int,
        session: AsyncSession = Depends(get_async_session),
        token: dict = Depends(verify_token),
):
    if token is None:
        raise HTTPException(status_code=401, detail='Token not provided!')

    user_id = token.get('user_id')
    result = await session.execute(
        select(user_role).where(
            user_role.c.user_id == user_id,
            user_role.c.role_name == 'admin'
        )
    )

    if not result.scalar():
        raise HTTPException(status_code=status.HTTP_405_METHOD_NOT_ALLOWED)

    try:
        out_file = f'files/{file_upload.filename}'
        async with aiofiles.open(f'uploads/{out_file}', 'wb') as f:
            content = await file_upload.read()
            await f.write(content)
        code = secrets.token_hex(32)
        insert_query = insert(file).values(
            tool_id=tool_id,
            file=out_file,
            hashcode=code
        )
        await session.execute(insert_query)
        await session.commit()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e)
    return {'success': True, 'message': 'Uploaded successfully'}


app.include_router(register_router, prefix='/auth')
app.include_router(router, prefix='/main')
