import os
import sys

from aiogram import Router, F
from aiogram.types import Message

from app.filters.admin import IsAdmin
from app.utils.logger import logger

router = Router(name="admin_restart")
router.message.filter(IsAdmin())


@router.message(F.text == "♻ Restart")
async def restart_bot(message: Message):
    """
    Botni qayta ishga tushiradi. Eslatma: bu process-level restart, shuning
    uchun bot systemd/pm2/Docker kabi process manager ostida ishlashi tavsiya
    etiladi, aks holda restart'dan keyin process to'xtab qolishi mumkin.
    """
    await message.answer("♻ Bot qayta ishga tushirilmoqda...")
    logger.warning(f"Admin {message.from_user.id} botni restart qildi.")
    os.execv(sys.executable, [sys.executable] + sys.argv)
