import aiogram.types
from aiogram import BaseMiddleware

from backend.bot.commands import sessions, users_collection
from backend.api import async_api as api


class MyMiddleware(BaseMiddleware):
    async def __call__(self, handler, event:aiogram.types.Update, data):
        id = event.message.from_user.id
        if not sessions.get(id):
            session = await api.create_session()
            user_data = users_collection.find_one({"id": id})
            if user_data:
                await api.login(session, user_data["login"], user_data["password"])
                sessions[id] = session
        return await handler(event, data)