from aiogram import Bot, Dispatcher
from backend.bot.router import router
import logging
from backend.middleware.middleware import MyMiddleware

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
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
