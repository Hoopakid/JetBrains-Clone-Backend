from fastapi import Depends, HTTPException, APIRouter
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from utils.auth_utils import verify_token
from dals.dals import FileDAL, ToolDAL, ComboDAL, LikeDAL, CommentDAL, CartDAL
from database import get_async_session
from utils.utils import is_admin

delete_router = APIRouter()


@delete_router.delete('/delete-cart')
async def delete_tool_from_shopping_cart(
        tool_id: int,
        session: AsyncSession = Depends(get_async_session),
        token: dict = Depends(verify_token)
):
    if token is None:
        raise HTTPException(status_code=status.HTTP_405_METHOD_NOT_ALLOWED, detail='Token not provided!!!')

    user_id = token.get('user_id')
    obj = CartDAL(session, user_id)
    await obj.delete_tool(tool_id)
    return {"success": True, "status": status.HTTP_204_NO_CONTENT}


@delete_router.delete('/delete-file/{file_id}')
async def delete_file(
        file_id: int,
        session: AsyncSession = Depends(get_async_session),
        token: dict = Depends(verify_token),
):
    if token is None:
        raise HTTPException(status_code=401, detail='Token not provided!')

    user_id = token.get('user_id')
    if is_admin(user_id, session) is False:
        raise HTTPException(status_code=status.HTTP_405_METHOD_NOT_ALLOWED, detail="Method not allowed")

    try:
        return await FileDAL(session).delete_file(file_id)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f'{e}')


@delete_router.delete("/tool{tool_id}")
async def delete_tool(
        tool_id: int,
        session: AsyncSession = Depends(get_async_session),
        token: dict = Depends(verify_token)
):
    if token is None:
        raise HTTPException(status_code=401, detail='Token not provided!')

    user_id = token.get('user_id')
    if is_admin(user_id, session) is False:
        raise HTTPException(status_code=status.HTTP_405_METHOD_NOT_ALLOWED, detail="Method not allowed")

    try:
        return await ToolDAL(session).delete(tool_id)
    except Exception as e:
        raise HTTPException(detail=f"{e}", status_code=status.HTTP_400_BAD_REQUEST)


@delete_router.delete('/delete-combo')
async def delete_combo(
        combo_id: int,
        token: dict = Depends(verify_token),
        session: AsyncSession = Depends(get_async_session)
):
    if token is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Token not provided!')
    user_id = token.get('user_id')
    if is_admin(user_id, session) is False:
        raise HTTPException(status_code=status.HTTP_405_METHOD_NOT_ALLOWED, detail="Method not allowed")

    obj = ComboDAL(session)
    await obj.delete_combo(combo_id)
    return {
        "success": True,
        "detail": "Combo deleted successfully!!",
        "status": status.HTTP_204_NO_CONTENT
    }


@delete_router.delete('/tool-like/{tool_id}')
async def delete_like(
        tool_id: int,
        token: dict = Depends(verify_token),
        session: AsyncSession = Depends(get_async_session)
):
    if token is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Token not provided!')

    like_dal = LikeDAL(session)

    user_id = token.get('user_id')
    return await like_dal.delete_like(tool_id, user_id)


@delete_router.delete('/delete-comment{comment_id}')
async def delete_comment(
        comment_id: int,
        token: dict = Depends(verify_token),
        session: AsyncSession = Depends(get_async_session)
):
    if token is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Token not provided!')
    user_id = token.get('user_id')
    try:
        obj = CommentDAL(session)
        await obj.delete_comment(comment_id, user_id)
        return {"detail": "Comment deleted successfully", "status": status.HTTP_204_NO_CONTENT}
    except NoResultFound:
        raise HTTPException(detail='Not found!!!', status_code=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        raise HTTPException(detail=f'{e}', status_code=status.HTTP_400_BAD_REQUEST)
