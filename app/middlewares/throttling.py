"""
Flood/spam himoyasi uchun oddiy rate-limit middleware.
Har bir foydalanuvchi uchun oxirgi so'rov vaqtini xotirada saqlaydi
(TTLCache o'rniga soddalik uchun dict, 10 000+ user uchun ham yengil).
"""
import time
from typing import Callable, Dict, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import Message

from app.config import config


class ThrottlingMiddleware(BaseMiddleware):
    def __init__(self, rate_limit: float | None = None):
        self.rate_limit = rate_limit or config.rate_limit_seconds
        self.last_call: Dict[int, float] = {}

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any],
    ) -> Any:
        user_id = event.from_user.id if event.from_user else None
        if user_id is not None:
            now = time.monotonic()
            last = self.last_call.get(user_id, 0)
            if now - last < self.rate_limit:
                return  # so'rovni e'tiborsiz qoldiramiz (flood)
            self.last_call[user_id] = now

        return await handler(event, data)
