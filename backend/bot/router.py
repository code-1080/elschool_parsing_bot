from backend.bot.commands import router as bot_router
from aiogram import Router

router = Router()
router.include_router(bot_router)
