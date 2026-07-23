"""
Ban qilingan userlarni bloklovchi va majburiy obunani tekshiruvchi
middleware.

Ban tekshiruvi - avvalgidek.
Obuna tekshiruvi - YANGI: har bir xabar/tugma bosilganda ishlaydi, shuning
uchun foydalanuvchi biror kanaldan chiqib ketsa, bu keyingi har qanday
harakatda (faqat /start yoki "✅ Tekshirish" tugmasida emas) darhol
aniqlanadi.

/start va "check_subscription" callback'i bundan mustasno - ular
start.py da o'zlari to'liq boshqariladi (aks holda ikki marta bir xil
xabar chiqib ketishi mumkin edi).
"""
from typing import Callable, Dict, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery

from app.database import users_repo, admins_repo
from app.keyboards.inline import subscription_keyboard
from app.services.subscription import get_not_subscribed_channels

EXEMPT_CALLBACKS = {"check_subscription"}


def _is_start_command(message: Message) -> bool:
    if not message.text:
        return False
    first_word = message.text.strip().split()[0]
    return first_word.split("@")[0] == "/start"


class BanCheckMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        user = getattr(event, "from_user", None)
        if user is None:
            return await handler(event, data)

        is_admin = await admins_repo.is_admin(user.id)

        # --- 1. Ban tekshiruvi (adminlar hech qachon banlanmaydi) ---
        if not is_admin and await users_repo.is_banned(user.id):
            return

        # Adminlar majburiy obunadan ham ozod - o'z kanallariga a'zo
        # bo'lmagan holatda ham panelga kira olishlari kerak.
        if is_admin:
            return await handler(event, data)

        # --- 2. Majburiy obuna tekshiruvi (har bir harakatda) ---
        if isinstance(event, Message) and _is_start_command(event):
            return await handler(event, data)  # /start o'zi tekshiradi

        if isinstance(event, CallbackQuery) and event.data in EXEMPT_CALLBACKS:
            return await handler(event, data)  # check_subscription o'zi tekshiradi

        bot = data.get("bot")
        not_subscribed = await get_not_subscribed_channels(bot, user.id)

        if not_subscribed:
            text = (
                "❌ Botdan foydalanishni davom ettirish uchun quyidagi "
                "kanallarga obuna bo'ling."
            )
            keyboard = subscription_keyboard(not_subscribed)

            if isinstance(event, CallbackQuery):
                await event.answer(
                    "❌ Siz kanal(lar)dan chiqib ketgansiz. Qayta obuna bo'ling.",
                    show_alert=True,
                )
                try:
                    await event.message.answer(text, reply_markup=keyboard)
                except Exception:
                    pass
            elif isinstance(event, Message):
                await event.answer(text, reply_markup=keyboard)

            return  # handlerga o'tkazilmaydi

        return await handler(event, data)