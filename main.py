import os.path
import secrets
import aiofiles
import starlette.status as status

from pathlib import Path

from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert, update
from sqlalchemy.sql import exists
from sqlalchemy.exc import NoResultFound

from fastapi import FastAPI, APIRouter, Depends, UploadFile
from fastapi.exceptions import HTTPException
from fastapi.responses import FileResponse

from auth.auth import register_router
from auth.utils import verify_token
from database import get_async_session
from models.models import tools, payment_model, LifeTimeEnum, users_data, user_role, file, tools, user_payment, \
    StatusEnum, user_coupon
from schemes import PaymentModel, UserPayment, ToolCreate
    StatusEnum, user_coupon, user_custom_coupon
from schemes import PaymentModel, UserPayment, GetLicenceCustomScheme
from utils import generate_coupon

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.sql import delete, update
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
        if if_payment.scalar():
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
        user_payment_id: int,
        tool_id: int,
        session: AsyncSession = Depends(get_async_session),
        token: dict = Depends(verify_token)
):
    try:
        if_tool_query = select(tools).where(tools.c.id == tool_id)
        if_tool = await session.execute(if_tool_query)
        if if_tool is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Tool not found')

        user_id = token.get('user_id')

        if_payment_query = select(user_payment).where(
            (user_payment.c.user_id == user_id) & (user_payment.c.id == user_payment_id)
        )
        if_payment = await session.execute(if_payment_query)
        user_payment_result = if_payment.one()
        if not user_payment_result:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Payment not found')
        coupon = generate_coupon(user_id, tool_id)

        payment_id = user_payment_result[1]
        payment_query_for_lifetime = select(payment_model).where(payment_model.c.id == payment_id)
        payment__result = await session.execute(payment_query_for_lifetime)
        payment_result = payment__result.one()

        month_or_year = str(payment_result[3])[13:]
        days = 30 if month_or_year == 'month' else 365

        lifetime = datetime.utcnow() + timedelta(days=days)

        insert_coupon_query = insert(user_coupon).values(
            coupon=coupon,
            user_id=user_id,
            lifetime=lifetime
        )

        await session.execute(insert_coupon_query)

        await session.commit()

        return {"status": status.HTTP_200_OK, "coupon": coupon}
    except Exception as e:
        raise HTTPException(detail=f'{e}', status_code=status.HTTP_400_BAD_REQUEST)


@router.get('/get-licence-custom-code')
async def get_licence_custom_code(
        user_payment_id: int,
        tool_id: int,
        phone_number: int,
        session: AsyncSession = Depends(get_async_session),
        token: dict = Depends(verify_token)
):
    try:
        phone_number_query = select(user_custom_coupon).where(user_custom_coupon.c.phone_number == phone_number)
        phone_number__result = await session.execute(phone_number_query)
        phone_number_result = phone_number__result.one()
        if phone_number_result:
            raise HTTPException(detail='You can get only 1 coupon for 1 phone number',
                                status_code=status.HTTP_400_BAD_REQUEST)

        user_id = token.get('user_id')

        if_tool_query = select(tools).where(tools.c.id == tool_id)
        if_tool = await session.execute(if_tool_query)
        if not if_tool.scalar():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Tool not found')

        if_payment_query = select(user_payment).where(
            (user_payment.c.user_id == user_id) & (user_payment.c.id == user_payment_id)
        )
        coupon = generate_coupon(user_id, tool_id)
        if_payment = await session.execute(if_payment_query)
        user_payment_result = if_payment.first()
        if not user_payment_result:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Payment not found')

        payment_id = user_payment_result[1]
        payment_query_for_lifetime = select(payment_model).where(payment_model.c.id == payment_id)
        payment__result = await session.execute(payment_query_for_lifetime)
        payment_result = payment__result.first()

        month_or_year = str(payment_result[3])[13:]
        days = 30 if month_or_year == 'month' else 365

        lifetime = datetime.utcnow() + timedelta(days=days)

        insert_coupon_query = insert(user_custom_coupon).values(
            user_id=user_id,
            phone_number=phone_number,
            tool_id=tool_id,
            coupon=coupon,
            lifetime=lifetime
        )

        await session.execute(insert_coupon_query)

        await session.commit()

        return {"status": status.HTTP_200_OK, "coupon": coupon}
    except Exception as e:
        raise HTTPException(detail=f'{e}', status_code=status.HTTP_400_BAD_REQUEST)


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
            hash=code
        )
        await session.execute(insert_query)
        await session.commit()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e)
    return {'success': True, 'message': 'Uploaded successfully'}


@app.post("/tool")
async def create_tool(tool_update: ToolCreate, session: AsyncSession = Depends(get_async_session), token: dict = Depends(verify_token)):
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
        new_tool = tools.insert().values(tool_name=tool_update.tool_name, monthly_fee=tool_update.monthly_fee, yearly_fee=tool_update.yearly_fee)
        await session.execute(new_tool)
        await session.commit()
        return {"message": "Tool created successfully"}
    except Exception as e:
        raise HTTPException(detail=f"{e}")

@app.get("/tool{tool_id}")
async def read_tool(tool_id: int, session: AsyncSession = Depends(get_async_session), token: dict = Depends(verify_token)):
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
        query = tools.select().where(tools.c.id == tool_id)
        result = await session.execute(query)
        tool = result.fetchone()

        if tool is None:
            raise HTTPException(status_code=404, detail="Tool not found")

        return tool
    except Exception as e:
        raise HTTPException(detail=f"{e}")

@app.put("/tool{tool_id}")
async def update_tool(tool_update: ToolCreate, session: AsyncSession = Depends(get_async_session), token: dict = Depends(verify_token)):
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
        query = update(tools).where(tools.c.id == tool_update.tool_id).values(tool_name=tool_update.tool_name, monthly_fee=tool_update.monthly_fee, yearly_fee=tool_update.yearly_fee)
        result = await session.execute(query)
        await session.commit()

        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Tool not found")

        return {"message": "Tool updated successfully"}
    except SQLAlchemyError as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail="Database error")

@app.delete("/tool{tool_id}")
async def delete_tool(tool_id: int, session: AsyncSession = Depends(get_async_session), token: dict = Depends(verify_token)):
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
        query = delete(tools).where(tools.c.id == tool_id)
        result = await session.execute(query)
        await session.commit()

        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Tool not found")

        return {"message": "Tool deleted successfully"}
    except SQLAlchemyError as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail="Database error")

@router.get('/download-file{hashcode}')
async def download_file(
        hashcode: str,
        session: AsyncSession = Depends(get_async_session),
):
    if hashcode is None:
        raise HTTPException(status_code=400, detail='Invalid hashcode')

    try:
        query = select(file).where(file.c.hash == hashcode)
        file_data = await session.execute(query)
        data = file_data.one()
        BASEDIR = os.path.dirname(os.path.abspath(__file__))
        file_url = os.path.join(BASEDIR, f'uploads/{data.file}')
        file_name = data.file.split('/')[-1]

    except Exception as e:
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Not Found')

    return FileResponse(path=file_url, media_type='application/octet-stream', filename=file_name)


app.include_router(register_router, prefix='/auth')
app.include_router(router, prefix='/main')



