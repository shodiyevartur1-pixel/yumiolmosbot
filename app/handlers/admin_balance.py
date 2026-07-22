from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.filters.admin import IsAdmin
from app.database import users_repo
from app.database.db import db
from app.keyboards.reply import cancel_keyboard, admin_menu
from app.states.states import AdminAddBalanceStates, AdminSubtractBalanceStates
from app.utils.logger import logger

router = Router(name="admin_balance")
router.message.filter(IsAdmin())

CANCEL_TEXT = "🚫 Bekor qilish"


async def _resolve_user(query: str):
    query = query.strip().lstrip("@")
    if query.isdigit():
        return await users_repo.get_user(int(query))
    user = await users_repo.get_user_by_wallet(query)
    return user


@router.message(F.text == "➕ Userga almaz qo'shish")
async def start_add_balance(message: Message, state: FSMContext):
    await state.set_state(AdminAddBalanceStates.waiting_user)
    await message.answer(
        "👤 Foydalanuvchi Telegram ID yoki Wallet ID sini kiriting:",
        reply_markup=cancel_keyboard(),
    )


@router.message(F.text == "➖ Userdan almaz ayirish")
async def start_subtract_balance(message: Message, state: FSMContext):
    await state.set_state(AdminSubtractBalanceStates.waiting_user)
    await message.answer(
        "👤 Foydalanuvchi Telegram ID yoki Wallet ID sini kiriting:",
        reply_markup=cancel_keyboard(),
    )


@router.message(StateFilter(AdminAddBalanceStates.waiting_user), F.text == CANCEL_TEXT)
@router.message(StateFilter(AdminAddBalanceStates.waiting_amount), F.text == CANCEL_TEXT)
@router.message(StateFilter(AdminSubtractBalanceStates.waiting_user), F.text == CANCEL_TEXT)
@router.message(StateFilter(AdminSubtractBalanceStates.waiting_amount), F.text == CANCEL_TEXT)
async def cancel_balance_change(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ Bekor qilindi.", reply_markup=admin_menu())


@router.message(StateFilter(AdminAddBalanceStates.waiting_user))
async def process_add_balance_user(message: Message, state: FSMContext):
    user = await _resolve_user(message.text)
    if user is None:
        await message.answer("❌ Foydalanuvchi topilmadi. Qaytadan kiriting.")
        return

    await state.update_data(target_user_id=user["user_id"])
    await state.set_state(AdminAddBalanceStates.waiting_amount)
    await message.answer(f"💎 {user['user_id']} ga necha Yumi Almaz qo'shmoqchisiz?")


@router.message(StateFilter(AdminAddBalanceStates.waiting_amount))
async def process_add_balance_amount(message: Message, state: FSMContext):
    if not message.text.strip().isdigit():
        await message.answer("❌ Iltimos, faqat son kiriting.")
        return

    amount = int(message.text.strip())
    data = await state.get_data()
    target_user_id = data["target_user_id"]

    await users_repo.add_balance(target_user_id, amount)
    await state.clear()
    logger.info(f"Admin {message.from_user.id} userga balans qo'shdi: {target_user_id} +{amount}")
    await message.answer(f"✅ {amount} 💎 qo'shildi.", reply_markup=admin_menu())

    try:
        await message.bot.send_message(
            target_user_id, f"💎 Balansingizga {amount} Yumi Almaz qo'shildi."
        )
    except Exception:
        pass


@router.message(StateFilter(AdminSubtractBalanceStates.waiting_user))
async def process_subtract_balance_user(message: Message, state: FSMContext):
    user = await _resolve_user(message.text)
    if user is None:
        await message.answer("❌ Foydalanuvchi topilmadi. Qaytadan kiriting.")
        return

    await state.update_data(target_user_id=user["user_id"])
    await state.set_state(AdminSubtractBalanceStates.waiting_amount)
    await message.answer(
        f"💎 {user['user_id']} dan necha Yumi Almaz ayirmoqchisiz? "
        f"(joriy balans: {user['balance']})"
    )


@router.message(StateFilter(AdminSubtractBalanceStates.waiting_amount))
async def process_subtract_balance_amount(message: Message, state: FSMContext):
    if not message.text.strip().isdigit():
        await message.answer("❌ Iltimos, faqat son kiriting.")
        return

    amount = int(message.text.strip())
    data = await state.get_data()
    target_user_id = data["target_user_id"]

    async with db.transaction() as conn:
        success = await users_repo.subtract_balance_atomic(target_user_id, amount, conn)

    await state.clear()
    if not success:
        await message.answer("❌ Foydalanuvchi balansi yetarli emas.", reply_markup=admin_menu())
        return

    logger.info(f"Admin {message.from_user.id} userdan balans ayirdi: {target_user_id} -{amount}")
    await message.answer(f"✅ {amount} 💎 ayirildi.", reply_markup=admin_menu())

    try:
        await message.bot.send_message(
            target_user_id, f"⚠ Balansingizdan {amount} Yumi Almaz ayirildi."
        )
    except Exception:
        pass
