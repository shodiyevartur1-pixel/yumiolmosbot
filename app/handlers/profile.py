from aiogram import Router, F
from aiogram.types import Message

from app.database import users_repo, referrals_repo

router = Router(name="profile")


@router.message(F.text == "👤 Profil")
async def show_profile(message: Message):
    user = await users_repo.get_user(message.from_user.id)
    if user is None:
        await message.answer("Iltimos, avval /start buyrug'ini bosing.")
        return

    ref_count = await referrals_repo.count_referrals(user["user_id"])
    registered_at = user["registered_at"][:10]

    username_line = f"@{user['username']}" if user["username"] else "-"
    text = (
        "👤 <b>Sizning profilingiz</b>\n\n"
        f"Ism: {user['first_name'] or '-'}\n"
        f"Username: {username_line}\n"
        f"Telegram ID: <code>{user['user_id']}</code>\n"
        f"💎 Balans: {user['balance']}\n"
        f"👥 Referallar soni: {ref_count}\n"
        f"📅 Ro'yxatdan o'tgan sana: {registered_at}\n"
    )
    await message.answer(text)
