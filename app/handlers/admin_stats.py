from aiogram import Router, F
from aiogram.types import Message

from app.filters.admin import IsAdmin
from app.database import users_repo, referrals_repo, withdraws_repo, transfers_repo

router = Router(name="admin_stats")
router.message.filter(IsAdmin())


@router.message(F.text == "👤 Statistika")
async def show_stats(message: Message):
    total_users = await users_repo.count_users()
    today_users = await users_repo.count_today_users()

    text = (
        "📊 <b>Umumiy statistika</b>\n\n"
        f"👥 Jami foydalanuvchilar: {total_users}\n"
        f"🆕 Bugungi ro'yxatdan o'tganlar: {today_users}\n"
    )
    await message.answer(text)


@router.message(F.text == "📈 Aktiv userlar")
async def show_active_users(message: Message):
    total_users = await users_repo.count_users()
    await message.answer(f"📈 Jami aktiv (bloklanmagan) foydalanuvchilar: {total_users}")


@router.message(F.text == "📅 Bugungi userlar")
async def show_today_users(message: Message):
    today_users = await users_repo.count_today_users()
    await message.answer(f"📅 Bugun ro'yxatdan o'tganlar soni: {today_users}")


@router.message(F.text == "📊 Referral statistikasi")
async def show_referral_stats(message: Message):
    top = await referrals_repo.get_top_referrers(limit=10)
    if not top:
        await message.answer("Hozircha referallar mavjud emas.")
        return

    lines = ["📊 <b>Referral statistikasi (TOP 10)</b>\n"]
    for i, row in enumerate(top, start=1):
        name = row["first_name"] or (f"@{row['username']}" if row["username"] else f"ID{row['user_id']}")
        lines.append(f"{i}. {name} — {row['ref_count']} ta")

    await message.answer("\n".join(lines))


@router.message(F.text == "📜 Withdrawal history")
async def show_withdrawal_history(message: Message):
    withdraws = await withdraws_repo.get_all_withdraws(limit=20)
    if not withdraws:
        await message.answer("Hozircha yechish so'rovlari yo'q.")
        return

    labels = {"pending": "⏳", "approved": "✅", "rejected": "❌"}
    lines = ["📜 <b>So'nggi 20 ta yechish so'rovi</b>\n"]
    for w in withdraws:
        who = f"@{w['username']}" if w["username"] else w["wallet_id"]
        lines.append(
            f"{labels.get(w['status'], '')} {w['created_at'][:16]} | {who} | {w['amount']} 💎"
        )

    text = "\n".join(lines)
    if len(text) > 4000:
        for i in range(0, len(text), 4000):
            await message.answer(text[i:i + 4000])
    else:
        await message.answer(text)


@router.message(F.text == "📦 Transfer history")
async def show_transfer_history(message: Message):
    transfers = await transfers_repo.get_all_transfers(limit=20)
    if not transfers:
        await message.answer("Hozircha o'tkazmalar yo'q.")
        return

    lines = ["📦 <b>So'nggi 20 ta o'tkazma</b>\n"]
    for t in transfers:
        lines.append(
            f"{t['created_at'][:16]} | {t['sender_wallet']} → {t['receiver_wallet']} | {t['amount']} 💎"
        )

    text = "\n".join(lines)
    if len(text) > 4000:
        for i in range(0, len(text), 4000):
            await message.answer(text[i:i + 4000])
    else:
        await message.answer(text)
