from fastapi import Depends, HTTPException, APIRouter
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from utils.auth_utils import verify_token
from dals.dals import ComboDAL, ToolDAL, CommentDAL
from database import get_async_session
from utils.utils import is_admin

patch_router = APIRouter()


@patch_router.patch("/tool{tool_id}")
async def update_tool(
        tool_id: int,
        tool_name: str = None,
        monthly_fee: float = None,
        yearly_fee: float = None,
        session: AsyncSession = Depends(get_async_session),
        token: dict = Depends(verify_token)
):
    user_id = token.get('user_id')
    if is_admin(user_id, session) is False:
        raise HTTPException(status_code=status.HTTP_405_METHOD_NOT_ALLOWED, detail="Method not allowed")

    try:
         await ToolDAL(session).update_tool(tool_id, tool_name, monthly_fee, yearly_fee)
    except Exception as e:
        raise HTTPException(detail=f"{e}", status_code=status.HTTP_400_BAD_REQUEST)


@patch_router.patch('/edit-combo')
async def edit_combo(
        new_combo_name: str,
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
    await obj.edit_combo(new_combo_name, combo_id)
    return {
        "success": True,
        "detail": "Combo updated successfully!!!",
        "status": status.HTTP_200_OK
    }


@patch_router.patch('/edit-comment/{comment_id}')
async def edit_comment_handler(
        comment_id: int,
        new_content: str = None,
        stts: int = None,
        token: dict = Depends(verify_token),
        session: AsyncSession = Depends(get_async_session)
):
    if token is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Token not provided!')

    user_id = token.get('user_id')

    comment_dal = CommentDAL(session)
    await comment_dal.edit_comment(comment_id=comment_id, user_id=user_id, new_content=new_content, stts=stts)

    return {"detail": "Comment edited successfully", "status": status.HTTP_200_OK}
