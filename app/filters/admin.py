from aiogram.filters import BaseFilter
from aiogram.types import Message

from app.database import admins_repo


class IsAdmin(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        return await admins_repo.is_admin(message.from_user.id)
