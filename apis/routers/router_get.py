from datetime import timedelta, datetime

from fastapi import Depends, HTTPException, APIRouter
from sqlalchemy import select, insert, delete
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from utils.auth_utils import verify_token
from dals.dals import CartDAL, ComboDAL
from database import get_async_session
from models.models import user_coupon, tools, user_payment, payment_model, users_data, user_custom_coupon
from tasks.coupon_tasks.end_coupon import end_coupon_time
from tasks.coupon_tasks.end_custom_coupon import end_custom_coupon_time
from tasks.email_tasks.message import send_mail_task
from utils.utils import generate_coupon

get_router = APIRouter()


@get_router.get('/cart-data')
async def cart_data(
        token: dict = Depends(verify_token),
        session: AsyncSession = Depends(get_async_session)
):
    if token is None:
        raise HTTPException(status_code=status.HTTP_405_METHOD_NOT_ALLOWED, detail='Token not provided!!!')

    user_id = token.get('user_id')
    try:
        obj = CartDAL(session, user_id)
        payment_list = await obj.get_tool()
        return payment_list

    except Exception as e:
        raise HTTPException(detail=f'{e}', status_code=status.HTTP_400_BAD_REQUEST)


@get_router.get('/get-licence-code')
async def get_licence_code(
        user_payment_id: int,
        tool_id: int,
        session: AsyncSession = Depends(get_async_session),
        token: dict = Depends(verify_token)
):
    user_id = token.get('user_id')
    coupon = generate_coupon(user_id, tool_id)
    try:
        if_exist_query = select(user_coupon).where(
            (user_coupon.c.user_id == user_id) &
            (user_coupon.c.coupon == coupon) &
            (user_coupon.c.tool_id == tool_id)
        )
        result_exists = await session.execute(if_exist_query)
        if result_exists.fetchone():
            raise HTTPException(status_code=status.HTTP_204_NO_CONTENT,
                                detail='You have received a coupon. Click see active coupons to view')

        if_tool_query = select(tools).where(tools.c.id == tool_id)
        if_tool = await session.execute(if_tool_query)
        if not if_tool.fetchone():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Tool not found')

        if_payment_query = select(user_payment).where(
            (user_payment.c.user_id == user_id) & (user_payment.c.id == user_payment_id)
        )
        if_payment = await session.execute(if_payment_query)
        user_payment_result = if_payment.fetchone()
        if not user_payment_result:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Payment not found')

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
        await end_coupon_time(session)

        delete_from_user_payment_query = delete(payment_model).where(
            (payment_model.c.tool_id == tool_id) &
            (payment_model.c.user_id == user_id)
        )

        await session.execute(delete_from_user_payment_query)

        user_email_query = select(users_data).where(users_data.c.id == user_id)

        res = await session.execute(user_email_query)
        res_value = res.fetchone()[3]
        send_mail_task.apply_async(args=(res_value, coupon))

        await session.execute(insert_coupon_query)

        await session.commit()

        return {"status": status.HTTP_200_OK, "coupon": coupon}
    except Exception as e:
        raise HTTPException(detail=f'{e}', status_code=status.HTTP_400_BAD_REQUEST)


@get_router.get('/get-licence-custom-code')
async def get_licence_custom_code(
        user_payment_id: int,
        tool_id: int,
        phone_number: int,
        session: AsyncSession = Depends(get_async_session),
        token: dict = Depends(verify_token)
):
    user_id = token.get('user_id')
    coupon = generate_coupon(user_id, tool_id)
    try:
        if_exist_query = select(user_custom_coupon).where(
            (user_custom_coupon.c.user_id == user_id) &
            (user_custom_coupon.c.coupon == coupon) &
            (user_custom_coupon.c.tool_id == tool_id)
        )
        result_exists = await session.execute(if_exist_query)
        if result_exists.fetchone():
            raise HTTPException(status_code=status.HTTP_204_NO_CONTENT,
                                detail='You have received a coupon. Click see active coupons to view')

        phone_number_query = select(user_custom_coupon).where(user_custom_coupon.c.phone_number == phone_number)
        phone_number__result = await session.execute(phone_number_query)
        phone_number_result = phone_number__result.one()
        if phone_number_result:
            raise HTTPException(detail='You can get only 1 coupon for 1 phone number',
                                status_code=status.HTTP_400_BAD_REQUEST)

        if_tool_query = select(tools).where(tools.c.id == tool_id)
        if_tool = await session.execute(if_tool_query)
        if not if_tool.scalar():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Tool not found')

        if_payment_query = select(user_payment).where(
            (user_payment.c.user_id == user_id) & (user_payment.c.id == user_payment_id)
        )
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

        await end_custom_coupon_time(session)

        delete_from_user_payment_query = delete(payment_model).where(
            (payment_model.c.tool_id == tool_id) &
            (payment_model.c.user_id == user_id)
        )

        await session.execute(delete_from_user_payment_query)

        user_email_query = select(users_data).where(users_data.c.id == user_id)

        res = await session.execute(user_email_query)
        res_value = res.fetchone()[3]
        send_mail_task.apply_async(args=(res_value, coupon))

        await session.commit()

        return {"status": status.HTTP_200_OK, "coupon": coupon}
    except Exception as e:
        raise HTTPException(detail=f'{e}', status_code=status.HTTP_400_BAD_REQUEST)


@get_router.get('/see-account-detail')
async def see_detail(
        token: dict = Depends(verify_token),
        session: AsyncSession = Depends(get_async_session)
):
    user_id = token.get('user_id')
    try:
        user_payment_query = select(user_payment).where(
            user_payment.c.user_id == user_id
        )
        result = await session.execute(user_payment_query)
        user_payment_data = result.fetchone()
        if user_payment_data:
            payment_id = user_payment_data[1]
            payment_query = select(payment_model).where(
                payment_model.c.id == payment_id
            )
            payment__data = await session.execute(payment_query)
            payment_data = payment__data.fetchone()

            tool_query = select(tools).where(tools.c.id == payment_data[2])
            tool__data = await session.execute(tool_query)
            tool_data = tool__data.fetchone()

            user_query = select(users_data).where(users_data.c.id == user_id)
            user__data = await session.execute(user_query)
            user_data = user__data.fetchone()

            coupon_query = select(user_coupon).where(
                (user_coupon.c.user_id == user_id) &
                (user_coupon.c.tool_id == tool_data[0])
            )
            coupon__data = await session.execute(coupon_query)
            coupon_data = coupon__data.fetchone()
            coupon = None
            coupon_lifetime = None
            if coupon_data:
                coupon = coupon_data[1]
                coupon_lifetime = coupon_data[5]

            custom_coupon_query = select(user_custom_coupon).where(
                (user_custom_coupon.c.user_id == user_id) &
                (user_custom_coupon.c.tool_id == tool_data[0])
            )
            custom_coupon__data = await session.execute(custom_coupon_query)
            custom_coupon_data = custom_coupon__data.fetchone()
            custom_coupon = None
            custom_coupon_lifetime = None
            phone_number = None
            if custom_coupon_data:
                custom_coupon = custom_coupon_data[1]
                custom_coupon_lifetime = custom_coupon_data[6]
                phone_number = custom_coupon_data[2]
            user_detail = {
                "user_id": user_data[0],
                "user_name": user_data[1],
                "tool_data": {
                    "tool_name": tool_data[1],
                    "fee_type": payment_data[3],
                    "status": user_payment_data[3],
                    "coupon": {
                        "coupon": coupon,
                        "billing_date": coupon_lifetime
                    },
                    "custom_coupon": {
                        "custom_coupon": custom_coupon,
                        "billing_date": custom_coupon_lifetime,
                        "phone_number": phone_number
                    },
                    "licenced_to": user_data[2],
                }
            }
            return {"data": user_detail}
    except Exception as e:
        raise HTTPException(detail=f'{e}', status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@get_router.get('/get-all-combos')
async def get_all_combos(
        token: dict = Depends(verify_token),
        session: AsyncSession = Depends(get_async_session)
):
    if token is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Token not provided!')
    user_id = token.get('user_id')
    combo_dal = ComboDAL(session)
    try:
        combos = await combo_dal.get_all_combos()
        return combos
    except HTTPException as e:
        raise HTTPException(detail=f'{e}', status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    finally:
        await session.close()
