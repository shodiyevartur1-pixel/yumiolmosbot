"""
Yopiq kanallardan kelayotgan a'zolik so'rovlarini (chat_join_request)
qayd qiladi. Bu handlerni asosiy dispatcher'ga ro'yxatdan o'tkazish kerak:

    from app.handlers import channel_join_requests
    dp.include_router(channel_join_requests.router)

Bot kanalda admin bo'lishi va "yangi a'zolarni tasdiqlash" huquqiga ega
bo'lishi shart, aks holda bu update botga kelmaydi.
"""
from datetime import datetime, timezone

from aiogram import Router
from aiogram.types import ChatJoinRequest

from app.database import join_requests_repo
from app.utils.logger import logger

router = Router(name="channel_join_requests")


@router.chat_join_request()
async def handle_join_request(update: ChatJoinRequest):
    now = datetime.now(timezone.utc).isoformat()
    await join_requests_repo.save_join_request(update.chat.id, update.from_user.id, now)
    logger.info(
        f"Join request qayd qilindi: chat={update.chat.id} user={update.from_user.id}"
    )