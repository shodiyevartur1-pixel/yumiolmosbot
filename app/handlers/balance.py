from aiogram import Router, F
from aiogram.types import Message

from app.database import users_repo

router = Router(name="balance")


@router.message(F.text == "💎 Balans")
async def show_balance(message: Message):
    user = await users_repo.get_user(message.from_user.id)
    if user is None:
        await message.answer("Iltimos, avval /start buyrug'ini bosing.")
        return

    await message.answer(f"💎 Sizning balansingiz: <b>{user['balance']}</b> Yumi Almaz")
