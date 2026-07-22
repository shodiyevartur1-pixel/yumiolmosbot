"""
Ban qilingan userlarni bloklovchi middleware.
"""
from typing import Callable, Dict, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from app.database import users_repo, admins_repo


class BanCheckMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        user = getattr(event, "from_user", None)
        if user is not None:
            # Adminlar hech qachon banlanmaydi (o'zlarini bloklab qo'yishmasin)
            if not await admins_repo.is_admin(user.id):
                if await users_repo.is_banned(user.id):
                    return
        return await handler(event, data)
