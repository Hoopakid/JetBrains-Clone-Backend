import secrets
import string

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.models import user_role


def generate_coupon(user_id: int, tool_id: int):
    words = string.ascii_uppercase + string.digits
    coupon = ''.join(secrets.choice(words) for _ in range(31))
    return f'{user_id}{coupon}{tool_id}'[::-1]


async def is_admin(user_id: int, session: AsyncSession):
    result = await session.execute(
        select(user_role).where(
            user_role.c.user_id == user_id,
            user_role.c.role_name == 'admin'
        )
    )

    if not result.scalar():
        return False
    return True
