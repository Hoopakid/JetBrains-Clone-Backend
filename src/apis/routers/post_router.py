from fastapi import Depends, HTTPException, UploadFile, APIRouter
from sqlalchemy import select, update, insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from utils.auth_utils import verify_token
from dals.dals import CartDAL, FileDAL, ToolDAL, ComboDAL, LikeDAL, CommentDAL
from database import get_async_session
from models.models import user_payment, payment_model, users_data, tools
from apis.routers.schemes import PaymentModel, ToolCreate, CommentScheme
from utils.utils import is_admin

post_router = APIRouter()


@post_router.post('/add-cart')
async def add_tool_shopping_cart(
        payment: PaymentModel,
        session: AsyncSession = Depends(get_async_session),
        token: dict = Depends(verify_token),
):
    if token is None:
        raise HTTPException(status_code=401, detail='Token not provided!')

    user_id = token.get('user_id')
    obj = CartDAL(session, user_id)
    await obj.add_cart(payment)
    return {"message": "Tool added to shopping cart!!!"}


@post_router.post('/payment/{payment_id}')
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


@post_router.post('/upload-file')
async def upload_file(
        file_upload: UploadFile,
        tool_id: int,
        session: AsyncSession = Depends(get_async_session),
        token: dict = Depends(verify_token),
):
    if token is None:
        raise HTTPException(status_code=401, detail='Token not provided!')

    user_id = token.get('user_id')
    if is_admin(user_id, session) is False:
        raise HTTPException(status_code=status.HTTP_405_METHOD_NOT_ALLOWED, detail="Method not allowed")

    try:
        return await FileDAL(session).upload_file(file_upload, tool_id)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e)


@post_router.post("/tool")
async def create_tool(
        tool_create: ToolCreate,
        session: AsyncSession = Depends(get_async_session),
        token: dict = Depends(verify_token)
):
    if token is None:
        raise HTTPException(status_code=401, detail='Token not provided!')

    user_id = token.get('user_id')
    if is_admin(user_id, session) is False:
        raise HTTPException(status_code=status.HTTP_405_METHOD_NOT_ALLOWED, detail="Method not allowed")
    try:
        tool_dal = ToolDAL(session)
        await tool_dal.create(tool_create)
        return {"message": "Tool created successfully"}
    except Exception as e:
        raise HTTPException(detail=f"{e}", status_code=status.HTTP_400_BAD_REQUEST)


@post_router.post('/create-combo')
async def create_combo(
        combo_name: str,
        token: dict = Depends(verify_token),
        session: AsyncSession = Depends(get_async_session)
):
    if token is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Token not provided!')
    user_id = token.get('user_id')
    if is_admin(user_id, session) is False:
        raise HTTPException(status_code=status.HTTP_405_METHOD_NOT_ALLOWED, detail="Method not allowed")

    obj = ComboDAL(session)
    await obj.create_combo(combo_name)
    return {
        "success": True,
        "detail": "Combo created successfully. It's time to add tools for this combo😉",
        "status": status.HTTP_201_CREATED
    }


@post_router.post('/add-tool-for-combo')
async def add_tool_combo(
        combo_id: int,
        tool_id: int,
        token: dict = Depends(verify_token),
        session: AsyncSession = Depends(get_async_session),
):
    if token is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Token not provided!')
    user_id = token.get('user_id')
    if await is_admin(user_id, session) is False:
        raise HTTPException(status_code=status.HTTP_405_METHOD_NOT_ALLOWED, detail="Method not allowed")

    try:
        obj = ComboDAL(session)
        await obj.add_tool_for_combo(combo_id, tool_id)
        return {"success": True, "detail": "Tool successfully added to combo with axia of 10 percentage",
                "status": status.HTTP_201_CREATED}
    except Exception as e:
        raise HTTPException(detail=f'{e}', status_code=status.HTTP_400_BAD_REQUEST)

    finally:
        await session.close()


@post_router.post('/tool-like/{tool_id}')
async def like_tool(
        tool_id: int,
        token: dict = Depends(verify_token),
        session: AsyncSession = Depends(get_async_session)
):
    if token is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Token not provided!')

    like_dal = LikeDAL(session)

    user_id = token.get('user_id')
    return await like_dal.like_tool(tool_id, user_id)


@post_router.post('/tool-comment')
async def comment_tool(
        comment_data: CommentScheme,
        token: dict = Depends(verify_token),
        session: AsyncSession = Depends(get_async_session)
):
    if token is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Token not provided!')
    user_id = token.get('user_id')
    try:
        obj = CommentDAL(session)
        await obj.create_comment(comment_data, user_id)
        return {"detail": "Commented successfully", "status": status.HTTP_200_OK}

    except IntegrityError:
        raise HTTPException(detail='User already commented this tool', status_code=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        raise HTTPException(detail=f'{e}', status_code=status.HTTP_400_BAD_REQUEST)
