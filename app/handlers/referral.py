from aiogram import Router, F
from aiogram.types import Message

from app.database import users_repo, referrals_repo, settings_repo
from app.keyboards.inline import referral_link_keyboard

router = Router(name="referral")


@router.message(F.text == "👥 Referal")
async def show_referral_menu(message: Message):
    user = await users_repo.get_user(message.from_user.id)
    if user is None:
        await message.answer("Iltimos, avval /start buyrug'ini bosing.")
        return

    bot_info = await message.bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start={user['user_id']}"

    total_refs = await referrals_repo.count_referrals(user["user_id"])
    today_refs = await referrals_repo.count_today_referrals(user["user_id"])
    bonus = await settings_repo.get_referral_bonus()
    total_bonus = total_refs * bonus

    text = (
        "👥 <b>Referal tizimi</b>\n\n"
        f"🔗 Sizning referal havolangiz:\n<code>{ref_link}</code>\n\n"
        f"👤 Referallar soni: {total_refs}\n"
        f"📅 Bugungi referallar: {today_refs}\n"
        f"💎 Jami bonus: {total_bonus}\n\n"
        f"Har bir taklif qilingan do'stingiz uchun {bonus} 💎 olasiz!\n\n"
        "🏆 Top referallar ro'yxatini ko'rish uchun /top buyrug'ini yuboring."
    )
    await message.answer(text, reply_markup=referral_link_keyboard(ref_link))


@router.message(F.text == "/top")
async def show_top_referrers(message: Message):
    top = await referrals_repo.get_top_referrers(limit=100)
    if not top:
        await message.answer("Hozircha referallar mavjud emas.")
        return

    lines = ["🏆 <b>TOP 100 Referral</b>\n"]
    for i, row in enumerate(top, start=1):
        name = row["first_name"] or (f"@{row['username']}" if row["username"] else f"ID{row['user_id']}")
        lines.append(f"{i}. {name} — {row['ref_count']} ta")

    text = "\n".join(lines)
    # Telegram xabar uzunligi cheklovi uchun bo'lib yuboramiz
    if len(text) > 4000:
        for i in range(0, len(text), 4000):
            await message.answer(text[i:i + 4000])
    else:
        await message.answer(text)
