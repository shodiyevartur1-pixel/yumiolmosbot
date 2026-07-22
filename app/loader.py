"""
Bot va Dispatcher obyektlarini yaratish.
main.py shu yerdan import qilib ishlatadi.
"""
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from app.config import config

bot = Bot(
    token=config.bot_token,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML),
)

# Katta yuklama ostida (10 000+ user) FSM holatlarini saqlash uchun
# MemoryStorage yetarli bo'ladi bitta process ichida; agar kelajakda
# ko'p worker/process kerak bo'lsa, RedisStorage'ga almashtirish tavsiya etiladi.
storage = MemoryStorage()

dp = Dispatcher(storage=storage)
