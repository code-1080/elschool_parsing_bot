from aiogram import Bot, Dispatcher
import logging

from backend.bot.router import router
from backend.middleware.middleware import MyMiddleware

import backend.db.db as db

import os
from dotenv import load_dotenv

import asyncio


load_dotenv()
TOKEN = os.getenv("TOKEN")

bot = Bot(token=TOKEN)

dp = Dispatcher()
dp.include_router(router)

dp.update.outer_middleware(MyMiddleware())

async def main():
    await db.setup_db()
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())