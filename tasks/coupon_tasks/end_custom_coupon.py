from datetime import datetime
from fastapi import Depends
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_async_session
from models.models import user_custom_coupon, EndTimeEnum
from tasks.config import celery


@celery.task(serializer='json')
async def end_custom_coupon_time(session: AsyncSession = Depends(get_async_session)):
    try:
        expired_coupons_query = select(user_custom_coupon).where(
            user_custom_coupon.c.lifetime <= datetime.utcnow,
            user_custom_coupon.c.status == EndTimeEnum.active
        )
        expired_coupons_result = await session.execute(expired_coupons_query)
        expired_coupons = expired_coupons_result.all()

        for coupon in expired_coupons:
            coupon_id = coupon[0]
            update_status_query = (
                update(user_custom_coupon)
                .where(user_custom_coupon.c.id == coupon_id)
                .values(status=EndTimeEnum.expired)
            )
            await session.execute(update_status_query)
        await session.commit()
    except Exception as e:
        print(f'{e}')
