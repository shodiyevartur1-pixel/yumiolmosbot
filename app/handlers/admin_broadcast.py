import asyncio
from datetime import datetime, timezone

from aiogram import Router, F
from aiogram.exceptions import TelegramForbiddenError, TelegramRetryAfter, TelegramBadRequest
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from app.filters.admin import IsAdmin
from app.database import users_repo
from app.database.db import db
from app.keyboards.reply import cancel_keyboard, admin_menu
from app.keyboards.inline import broadcast_confirm_keyboard
from app.states.states import AdminBroadcastStates
from app.utils.logger import logger

router = Router(name="admin_broadcast")
router.message.filter(IsAdmin())

CANCEL_TEXT = "🚫 Bekor qilish"


@router.message(F.text == "📢 Reklama yuborish")
async def start_broadcast(message: Message, state: FSMContext):
    await state.set_state(AdminBroadcastStates.waiting_content)
    await message.answer(
        "📢 Yubormoqchi bo'lgan xabarni yuboring (matn, rasm, video, animatsiya, "
        "hujjat yoki forward - barchasi qo'llab-quvvatlanadi):",
        reply_markup=cancel_keyboard(),
    )


@router.message(StateFilter(AdminBroadcastStates.waiting_content), F.text == CANCEL_TEXT)
async def cancel_broadcast(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ Bekor qilindi.", reply_markup=admin_menu())


@router.message(StateFilter(AdminBroadcastStates.waiting_content))
async def process_broadcast_content(message: Message, state: FSMContext):
    await state.update_data(chat_id=message.chat.id, message_id=message.message_id)
    await state.set_state(AdminBroadcastStates.confirm)
    await message.answer(
        "Yuqoridagi xabarni barcha foydalanuvchilarga yubormoqchimisiz?",
        reply_markup=broadcast_confirm_keyboard(),
    )


@router.callback_query(StateFilter(AdminBroadcastStates.confirm), F.data == "broadcast_cancel")
async def cancel_broadcast_callback(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Bekor qilindi.")
    await callback.answer()


@router.callback_query(StateFilter(AdminBroadcastStates.confirm), F.data == "broadcast_confirm")
async def confirm_broadcast(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    chat_id = data["chat_id"]
    message_id = data["message_id"]
    await state.clear()

    user_ids = await users_repo.get_all_user_ids()
    total = len(user_ids)
    sent = 0
    blocked = 0

    progress_msg = await callback.message.edit_text(f"⏳ Yuborilmoqda... 0/{total}")

    for i, user_id in enumerate(user_ids, start=1):
        try:
            await callback.bot.copy_message(
                chat_id=user_id, from_chat_id=chat_id, message_id=message_id
            )
            sent += 1
        except TelegramRetryAfter as e:
            await asyncio.sleep(e.retry_after)
            try:
                await callback.bot.copy_message(
                    chat_id=user_id, from_chat_id=chat_id, message_id=message_id
                )
                sent += 1
            except Exception:
                blocked += 1
        except (TelegramForbiddenError, TelegramBadRequest):
            blocked += 1
        except Exception as e:
            logger.warning(f"Broadcast xatoligi user={user_id}: {e}")
            blocked += 1

        if i % 25 == 0 or i == total:
            try:
                await progress_msg.edit_text(
                    f"⏳ Yuborilmoqda... {i}/{total}\n✅ Muvaffaqiyatli: {sent}\n🚫 Bloklagan: {blocked}"
                )
            except Exception:
                pass
        await asyncio.sleep(0.05)

    now = datetime.now(timezone.utc).isoformat()
    await db.conn.execute(
        """
        INSERT INTO broadcast_logs (admin_id, total, sent, blocked, created_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (callback.from_user.id, total, sent, blocked, now),
    )
    await db.conn.commit()

    await progress_msg.edit_text(
        f"✅ Yuborish yakunlandi.\n\nJami: {total}\nMuvaffaqiyatli: {sent}\nBloklagan: {blocked}"
    )
    await callback.message.answer("Admin panel:", reply_markup=admin_menu())