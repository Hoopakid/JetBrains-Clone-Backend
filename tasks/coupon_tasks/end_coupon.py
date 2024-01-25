
from fastapi import Depends
from sqlalchemy import update, select
from sqlalchemy.ext.asyncio import AsyncSession
from tasks.config import celery
from datetime import datetime

from database import get_async_session
from models.models import user_coupon, EndTimeEnum


@celery.task(serializer='json')
async def end_coupon_time(session: AsyncSession = Depends(get_async_session)):
    try:
        expired_coupons_query = select(user_coupon).where(
            user_coupon.c.lifetime <= datetime.utcnow,
            user_coupon.c.status == EndTimeEnum.active
        )
        expired_coupons_result = await session.execute(expired_coupons_query)
        expired_coupons = expired_coupons_result.all()

        for coupon in expired_coupons:
            coupon_id = coupon[0]
            update_status_query = (
                update(user_coupon)
                .where(user_coupon.c.id == coupon_id)
                .values(status=EndTimeEnum.expired)
            )
            await session.execute(update_status_query)
        await session.commit()
    except Exception as e:
        print(f'{e}')
