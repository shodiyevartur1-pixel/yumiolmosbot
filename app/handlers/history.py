from aiogram import Router, F
from aiogram.types import Message

from app.database import users_repo, transfers_repo, withdraws_repo

router = Router(name="history")

STATUS_LABELS = {
    "pending": "⏳ Kutilmoqda",
    "approved": "✅ Tasdiqlangan",
    "rejected": "❌ Bekor qilingan",
}


@router.message(F.text == "📜 Tarix")
async def show_history(message: Message):
    user = await users_repo.get_user(message.from_user.id)
    if user is None:
        await message.answer("Iltimos, avval /start buyrug'ini bosing.")
        return

    transfers = await transfers_repo.get_user_transfer_history(user["user_id"], limit=10)
    withdraws = await withdraws_repo.get_user_withdraw_history(user["user_id"], limit=10)

    # lines = ["📜 <b>So'nggi o'tkazmalar</b>\n"]
    # if transfers:
    #     for t in transfers:
    #         if t["from_user"] == user["user_id"]:
    #             lines.append(
    #                 f"➡ {t['created_at'][:16]} | -{t['amount']} 💎 → {t['receiver_wallet']}"
    #             )
    #         else:
    #             lines.append(
    #                 f"⬅ {t['created_at'][:16]} | +{t['amount']} 💎 ← {t['sender_wallet']}"
    #             )
    # else:
    #     lines.append("Hozircha o'tkazmalar yo'q.")

    lines = ["\n🎁 <b>So'nggi yechish so'rovlari</b>\n"]
    if withdraws:
        for w in withdraws:
            status = STATUS_LABELS.get(w["status"], w["status"])
            lines.append(f"{w['created_at'][:16]} | {w['amount']} 💎 | {status}")
    else:
        lines.append("Hozircha yechish so'rovlari yo'q.")

    text = "\n".join(lines)
    if len(text) > 4000:
        for i in range(0, len(text), 4000):
            await message.answer(text[i:i + 4000])
    else:
        await message.answer(text)
