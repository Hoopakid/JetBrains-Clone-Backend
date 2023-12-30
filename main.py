import secrets
import aiofiles
import starlette.status as status

from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert
from sqlalchemy.sql import exists

from fastapi import FastAPI, APIRouter, Depends, UploadFile
from fastapi.exceptions import HTTPException

from auth.auth import register_router
from auth.utils import verify_token
from database import get_async_session
from models.models import tool, payment_model, LifeTimeEnum, users_data, user_role, file
from schemes import PaymentModel, UserPayment

app = FastAPI(title='JetBrains', version='1.0.0')
router = APIRouter()


@router.post('/payment_model')
async def create_payment_model(payment: PaymentModel, session: AsyncSession = Depends(get_async_session),
                               token: dict = Depends(verify_token), ):
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


@router.post('/payment')
async def payment_user(payment: UserPayment, session: AsyncSession = Depends(get_async_session),
                       token: dict = Depends(verify_token)):
    user_id = token.get('user_id')
    payment_query = select(payment_model).where(
        (payment_model.c.id == payment.payment_id) & (payment_model.c.user_id == user_id)
    )
    if_payment = await session.execute(payment_query)
    if not if_payment.scalar():
        raise HTTPException(status_code=404, detail="Payment not found!!!")

    user__balance = await session.execute(select(users_data).where(users_data.c.id == user_id))
    return True


@router.post('upload-file')
async def upload_file(
        file_upload: UploadFile,
        tool_id: int,
        session: AsyncSession = Depends(get_async_session),
        token: dict = Depends(verify_token),
):
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
