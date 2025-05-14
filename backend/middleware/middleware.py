import aiogram.types
from aiogram import BaseMiddleware

from sqlalchemy import select

from backend.bot.commands import sessions
from backend.api import async_api as api
from backend.db.db import get_session
from backend.db.models.user import UserModel


class MyMiddleware(BaseMiddleware):
    async def __call__(self, handler, event:aiogram.types.Update, data):
        id = event.message.from_user.id

        if not sessions.get(id):
            session = await api.create_session()
            db_session = await get_session()
            result = await db_session.execute(
                select(UserModel).where(UserModel.telegram_id == id)
            )
            user_data = result.scalars().first()
            await db_session.close()
            if user_data:
                await api.login(session, user_data.elschool_login, user_data.elschool_password)
                sessions[id] = session
        return await handler(event, data)