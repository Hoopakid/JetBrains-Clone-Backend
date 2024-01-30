import os
import secrets
import aiofiles

from fastapi import Depends, UploadFile
from fastapi.exceptions import HTTPException
from fastapi.responses import FileResponse

from sqlalchemy import insert, select, update, delete
from sqlalchemy.exc import IntegrityError, NoResultFound

from sqlalchemy.ext.asyncio import AsyncSession

from starlette import status

from database import get_async_session
from models.models import tools, file, payment_model, combo, combo_products, tool_comments, tool_likes
from apis.routers.schemes import ToolCreate, PaymentModel, CommentScheme


# DAL is = Data Access Layer
class ToolDAL:
    def __init__(self, session: AsyncSession = Depends(get_async_session)):
        self.session = session

    async def get_all(self):
        try:
            query = select(tools)
            result = await self.session.execute(query)
            tools_list = result.fetchall()

            return [
                {
                    "id": tool[0],
                    "tool_name": tool[1],
                    "monthly_fee": tool[2],
                    "yearly_fee": tool[3]
                }
                for tool in tools_list
            ]
        except Exception as e:
            raise HTTPException(detail=f"{e}", status_code=status.HTTP_400_BAD_REQUEST)

    async def create(self, obj: ToolCreate):
        try:
            new_tool = insert(tools).values(
                tool_name=obj.tool_name,
                monthly_fee=obj.monthly_fee,
                yearly_fee=obj.yearly_fee
            )
            await self.session.execute(new_tool)
            await self.session.commit()
            return True
        except Exception as e:
            raise HTTPException(detail=f'{e}', status_code=status.HTTP_400_BAD_REQUEST)

    async def get_by_id(self, tool_id: int):
        try:
            query = select(tools).where(tools.c.id == tool_id)
            result = await self.session.execute(query)
            tool = result.fetchone()

            if tool is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tool not found")

            return {
                "id": tool[0],
                "tool_name": tool[1],
                "monthly_fee": tool[2],
                "yearly_fee": tool[3]
            }
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f'{e}')

    async def update_tool(self, tool_id: int, tool_name: str = None, monthly_fee: float = None,
                          yearly_fee: float = None):
        update_query = update(tools).where(tools.c.id == tool_id)

        try:
            query = select(tools).where(tools.c.id == tool_id)
            result = await self.session.execute(query)
            if result.rowcount == 0:
                raise HTTPException(detail="Tool not found!!!", status_code=status.HTTP_404_NOT_FOUND)
            if tool_name is not None:
                tool_query = update_query.values(
                    tool_name=tool_name
                )
                await self.session.execute(tool_query)
            if monthly_fee is not None:
                month_query = update_query.values(
                    monthly_fee=monthly_fee
                )
                await self.session.execute(month_query)
            if yearly_fee is not None:
                year_query = update_query.values(
                    yearly_fee=yearly_fee
                )
                await self.session.execute(year_query)
            await self.session.commit()
            return {"message": "Tool updated successfully"}
        except Exception as e:
            raise HTTPException(detail=f"{e}", status_code=status.HTTP_400_BAD_REQUEST)

    async def delete(self, tool_id: int):
        try:
            query = delete(tools).where(tools.c.id == tool_id)
            result = await self.session.execute(query)
            await self.session.commit()

            if result.rowcount == 0:
                raise HTTPException(status_code=404, detail="Tool not found")

            return {"message": "Tool deleted successfully"}
        except Exception as e:
            raise HTTPException(detail=f"{e}", status_code=status.HTTP_400_BAD_REQUEST)


class FileDAL:
    def __init__(self, session):
        self.session = session

    async def upload_file(self, file_upload: UploadFile, tool_id: int):
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
            ).returning(file.c.tool_id)
            result = await self.session.execute(insert_query)
            await self.session.commit()
            return {'success': True, 'message': 'Uploaded successfully', "tool_id": result.scalar()}
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e)

    async def delete_file(self, file_id: int):
        try:
            file_query = select(file).where(file.c.id == file_id)
            result = await self.session.execute(file_query)
            file_data = result.fetchone()

            if file_data is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")

            file_path = file_data[1]
            os.remove(f'uploads/{file_path}')

            delete_query = delete(file).where(file.c.id == file_id)
            await self.session.execute(delete_query)
            await self.session.commit()
            return {'status': status.HTTP_204_NO_CONTENT, 'message': 'File deleted successfully'}

        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f'{e}')

    async def download_file(self, hashcode: str):
        try:
            query = select(file).where(file.c.hash == hashcode)
            file_data = await self.session.execute(query)
            data = file_data.one()
            BASEDIR = os.path.dirname(os.path.abspath(__file__))
            file_url = os.path.join(BASEDIR, f'uploads/{data.file}')
            file_name = data.file.split('/')[-1]
            return FileResponse(path=file_url, media_type='application/octet-stream', filename=file_name)
        except Exception as e:
            return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'{e}')


class CartDAL:
    def __init__(self, session, user_id):
        self.session = session
        self.user_id = user_id

    async def add_cart(self, payment: PaymentModel):
        try:
            exist = await self.session.execute(
                select(payment_model).where(
                    (payment_model.c.user_id == self.user_id) &
                    (payment_model.c.tool_id == payment.tool_id)
                )
            )

            if exist.scalar() is not None:
                raise HTTPException(detail="Tool already exists in the shopping cart!",
                                    status_code=status.HTTP_204_NO_CONTENT)

            new_payment = insert(payment_model).values(
                user_id=self.user_id,
                tool_id=payment.tool_id,
                lifetime=payment.lifetime,
            )
            await self.session.execute(new_payment)
            await self.session.commit()
            return {"message": "Tool added to shopping cart!!!"}

        except Exception as e:
            raise HTTPException(status_code=500, detail=f'{e}')

    async def delete_tool(self, tool_id: int):
        try:
            delete_query = delete(payment_model).where(
                (payment_model.c.user_id == self.user_id) &
                (payment_model.c.tool_id == tool_id)
            )
            await self.session.execute(delete_query)
            await self.session.commit()
        except Exception as e:
            raise HTTPException(detail=f'{e}', status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

    async def get_tool(self):
        try:
            data_query = select(payment_model).where(
                payment_model.c.user_id == self.user_id
            )
            result = await self.session.execute(data_query)
            payments = result.all()

            payment_list = [
                {
                    'id': payment.id,
                    'user_id': payment.user_id,
                    'tool_id': payment.tool_id,
                    'lifetime': payment.lifetime.value,
                    'created_at': payment.created_at,
                }
                for payment in payments
            ]
            return {'payments': payment_list}
        except Exception as e:
            raise HTTPException(detail=f'{e}', status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ComboDAL:
    def __init__(self, session):
        self.session = session

    async def create_combo(self, combo_name: str):
        try:
            insert_query = insert(combo).values(
                combo_name=combo_name
            )
            await self.session.execute(insert_query)
            await self.session.commit()
        except Exception as e:
            raise HTTPException(detail=f'{e}', status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

    async def edit_combo(self, new_combo_name: str, combo_id: int):
        try:
            update_query = update(combo).where(
                combo.c.id == combo_id
            ).values(
                combo_name=new_combo_name
            )
            await self.session.execute(update_query)
            await self.session.commit()
        except Exception as e:
            raise HTTPException(detail=f'{e}', status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

    async def delete_combo(self, combo_id):
        try:
            delete_query = delete(combo).where(
                combo.c.id == combo_id
            )
            await self.session.execute(delete_query)
            await self.session.commit()
        except Exception as e:
            raise HTTPException(detail=f'{e}', status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

    async def get_all_combos(self):
        try:
            select_query = select(combo)
            result = await self.session.execute(select_query)
            combos = result.mappings().all()
            combo_tool_data = []
            for cmb in combos:
                combo_id = cmb['id']
                tool_query = select(combo_products).where(combo_products.c.combo_id == combo_id)
                tool_result = await self.session.execute(tool_query)
                tool_ids = [row[2] for row in tool_result.all()]

                tool_data_query = select(tools).where(tools.c.id.in_(tool_ids))
                tool_data_result = await self.session.execute(tool_data_query)
                tool_data = tool_data_result.mappings().all()

                combo_tool_data.append({
                    'combo': {
                        "combo_data": dict(cmb),
                        "related_tools": [dict(tool_datas) for tool_datas in tool_data]
                    },
                })

            return combo_tool_data
        except Exception as e:
            raise HTTPException(detail=f'{e}', status_code=status.HTTP_400_BAD_REQUEST)

    async def add_tool_for_combo(self, combo_id: int, tool_id: int):

        try:
            combo_query = select(combo).where(combo.c.id == combo_id)
            existing_combo = await self.session.execute(combo_query)
            if existing_combo.scalar() is None:
                raise HTTPException(detail=f'Combo with ID {combo_id} does not exist',
                                    status_code=status.HTTP_404_NOT_FOUND)

            fee_query = select(tools).where(tools.c.id == tool_id)
            result = await self.session.execute(fee_query)
            tool_data = result.fetchone()

            if tool_data is None:
                raise HTTPException(detail='Tool not found', status_code=status.HTTP_404_NOT_FOUND)

            combo_tool_query = select(combo_products).where(combo_products.c.combo_id == combo_id,
                                                            combo_products.c.tool_id == tool_id)
            existing_combo_tool = await self.session.execute(combo_tool_query)
            if existing_combo_tool.scalar() is not None:
                raise HTTPException(detail=f'Tool with ID {tool_id} already exists in combo with ID {combo_id}',
                                    status_code=status.HTTP_400_BAD_REQUEST)

            month_fee = tool_data[2]
            year_fee = tool_data[3]

            combo_query = select(combo).where(combo.c.id == combo_id)
            combo__data = await self.session.execute(combo_query)
            combo_data = combo__data.all()

            combo_tool_month_fee = []
            combo_tool_year_fee = []

            for tool in combo_data:
                combo_tool_month_fee.append(tool.monthly_fee)
                combo_tool_year_fee.append(tool.yearly_fee)

            combo_tool_month_fee.append(month_fee)
            combo_tool_year_fee.append(year_fee)

            average_month_fee = (
                    sum(combo_tool_month_fee) - (sum(combo_tool_month_fee) / 100 * 10)) if combo_tool_month_fee else 0
            average_year_fee = (
                    sum(combo_tool_year_fee) - (sum(combo_tool_year_fee) / 100 * 10)) if combo_tool_year_fee else 0

            insert_query = insert(combo_products).values(
                combo_id=combo_id,
                tool_id=tool_id
            )

            update_query = update(combo).where(combo.c.id == combo_id).values(
                monthly_fee=average_month_fee,
                yearly_fee=average_year_fee
            )
            await self.session.execute(update_query)
            await self.session.execute(insert_query)
            await self.session.commit()

        except Exception as e:
            raise HTTPException(detail=f'{e}', status_code=status.HTTP_400_BAD_REQUEST)

        finally:
            await self.session.close()


class CommentDAL:
    def __init__(self, session):
        self.session = session

    async def create_comment(self, comment_data: CommentScheme, user_id: int):
        try:
            tool_existing_query = select(tools).where(tools.c.id == comment_data.tool_id)
            tool_result = await self.session.execute(tool_existing_query)
            if tool_result.scalar() is None:
                raise HTTPException(detail='Tool not found!!!', status_code=status.HTTP_404_NOT_FOUND)

            insert_query = insert(tool_comments).values(
                user_id=user_id,
                tool_id=comment_data.tool_id,
                comment=comment_data.content,
                status=comment_data.status
            )
            await self.session.execute(insert_query)
            await self.session.commit()

        except IntegrityError:
            raise HTTPException(detail='User already commented this tool', status_code=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            raise HTTPException(detail=f'{e}', status_code=status.HTTP_400_BAD_REQUEST)

    async def delete_comment(self, comment_id: int, user_id: int):
        try:
            delete_query = delete(tool_comments).where(
                (tool_comments.c.id == comment_id) &
                (tool_comments.c.user_id == user_id)
            )
            delete_data = await self.session.execute(delete_query)
            if delete_data.scalar() is None:
                raise HTTPException(detail='Comment for user is not found!!!', status_code=status.HTTP_404_NOT_FOUND)

            await self.session.commit()
            return {"detail": "Comment deleted successfully", "status": status.HTTP_204_NO_CONTENT}
        except NoResultFound:
            raise HTTPException(detail='Not found!!!', status_code=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            raise HTTPException(detail=f'{e}', status_code=status.HTTP_400_BAD_REQUEST)

    async def edit_comment(self, comment_id: int, user_id: int, new_content: str = None, stts: int = None):
        try:
            comment_check_query = select(tool_comments).where(
                (tool_comments.c.id == comment_id) &
                (tool_comments.c.user_id == user_id)
            )
            comment_check_result = await self.session.execute(comment_check_query)
            existing_comment = comment_check_result.scalar()

            if existing_comment is None:
                raise HTTPException(detail='Comment not found or does not belong to the user!!!',
                                    status_code=status.HTTP_404_NOT_FOUND)
            update_values = {}
            if new_content is not None:
                update_values['comment'] = new_content
            if stts is not None:
                update_values['status'] = stts

            if not update_values:
                raise HTTPException(detail='No update parameters provided', status_code=status.HTTP_400_BAD_REQUEST)

            update_query = update(tool_comments).where(tool_comments.c.id == comment_id).values(update_values)
            update_data = await self.session.execute(update_query)

            if update_data.rowcount == 0:
                raise HTTPException(detail='Comment not found!!!', status_code=status.HTTP_404_NOT_FOUND)

            await self.session.commit()
            return {"detail": "Comment updated successfully", "status": status.HTTP_200_OK}

        except Exception as e:
            raise HTTPException(detail=f'{e}', status_code=status.HTTP_400_BAD_REQUEST)


class LikeDAL:
    def __init__(self, session):
        self.session = session

    async def like_tool(self, tool_id: int, user_id: int):
        try:
            tool_existing_query = select(tools).where(tools.c.id == tool_id)
            tool_result = await self.session.execute(tool_existing_query)
            if tool_result.scalar() is None:
                raise HTTPException(detail='Tool not found!!!', status_code=status.HTTP_404_NOT_FOUND)

            insert_query = insert(tool_likes).values(
                user_id=user_id,
                tool_id=tool_id,
            )
            await self.session.execute(insert_query)
            await self.session.commit()
            return {"detail": "Liked successfully", "status": status.HTTP_200_OK}

        except IntegrityError:
            raise HTTPException(detail='User already liked this tool', status_code=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            raise HTTPException(detail=f'{e}', status_code=status.HTTP_400_BAD_REQUEST)

    async def delete_like(self, tool_id: int, user_id: int):
        try:
            like_check_query = select(tool_likes).where(
                (tool_likes.c.tool_id == tool_id) &
                (tool_likes.c.user_id == user_id)
            )
            like_check_result = await self.session.execute(like_check_query)
            existing_like = like_check_result.scalar()

            if existing_like is None:
                raise HTTPException(detail='Like not found or does not belong to the user!!!',
                                    status_code=status.HTTP_404_NOT_FOUND)

            delete_query = delete(tool_likes).where(
                (tool_likes.c.tool_id == tool_id) &
                (tool_likes.c.user_id == user_id)
            )
            await self.session.execute(delete_query)
            await self.session.commit()
            return {"detail": "Like deleted successfully", "status": status.HTTP_204_NO_CONTENT}

        except Exception as e:
            raise HTTPException(detail=f'{e}', status_code=status.HTTP_400_BAD_REQUEST)
