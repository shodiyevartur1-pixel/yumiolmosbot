from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.filters.admin import IsAdmin
from app.database import users_repo, referrals_repo
from app.keyboards.reply import cancel_keyboard, admin_menu
from app.states.states import AdminSearchUserStates, AdminBanStates, AdminUnbanStates
from app.utils.logger import logger

router = Router(name="admin_users")
router.message.filter(IsAdmin())

CANCEL_TEXT = "🚫 Bekor qilish"


def _format_user_card(user, ref_count: int) -> str:
    username = f"@{user['username']}" if user["username"] else "-"
    status = "🚫 Bloklangan" if user["is_banned"] else "✅ Faol"
    return (
        f"👤 <b>{user['first_name'] or '-'}</b>\n"
        f"Username: {username}\n"
        f"Telegram ID: <code>{user['user_id']}</code>\n"
        f"Wallet ID: <code>{user['wallet_id']}</code>\n"
        f"💎 Balans: {user['balance']}\n"
        f"👥 Referallar: {ref_count}\n"
        f"📅 Ro'yxatdan o'tgan: {user['registered_at'][:10]}\n"
        f"Holat: {status}"
    )


@router.message(F.text == "🔍 User qidirish")
async def start_search_user(message: Message, state: FSMContext):
    await state.set_state(AdminSearchUserStates.waiting_query)
    await message.answer(
        "🔍 Telegram ID, Wallet ID, username yoki ism bo'yicha qidiring:",
        reply_markup=cancel_keyboard(),
    )


@router.message(StateFilter(AdminSearchUserStates.waiting_query), F.text == CANCEL_TEXT)
@router.message(StateFilter(AdminBanStates.waiting_user), F.text == CANCEL_TEXT)
@router.message(StateFilter(AdminUnbanStates.waiting_user), F.text == CANCEL_TEXT)
async def cancel_user_action(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ Bekor qilindi.", reply_markup=admin_menu())


@router.message(StateFilter(AdminSearchUserStates.waiting_query))
async def process_search_user(message: Message, state: FSMContext):
    result = await users_repo.search_user(message.text)
    await state.clear()

    if result is None:
        await message.answer("❌ Foydalanuvchi topilmadi.", reply_markup=admin_menu())
        return

    if isinstance(result, list):
        if not result:
            await message.answer("❌ Foydalanuvchi topilmadi.", reply_markup=admin_menu())
            return
        for user in result[:10]:
            ref_count = await referrals_repo.count_referrals(user["user_id"])
            await message.answer(_format_user_card(user, ref_count))
        await message.answer("Qidiruv yakunlandi.", reply_markup=admin_menu())
    else:
        ref_count = await referrals_repo.count_referrals(result["user_id"])
        await message.answer(_format_user_card(result, ref_count), reply_markup=admin_menu())


@router.message(F.text == "🚫 Ban")
async def start_ban(message: Message, state: FSMContext):
    await state.set_state(AdminBanStates.waiting_user)
    await message.answer(
        "🚫 Bloklamoqchi bo'lgan foydalanuvchi Telegram ID yoki Wallet ID sini kiriting:",
        reply_markup=cancel_keyboard(),
    )


@router.message(StateFilter(AdminBanStates.waiting_user))
async def process_ban(message: Message, state: FSMContext):
    query = message.text.strip().lstrip("@")
    user = await users_repo.get_user(int(query)) if query.isdigit() else await users_repo.get_user_by_wallet(query)
    await state.clear()

    if user is None:
        await message.answer("❌ Foydalanuvchi topilmadi.", reply_markup=admin_menu())
        return

    await users_repo.set_ban(user["user_id"], True)
    logger.info(f"Admin {message.from_user.id} userni bloklladi: {user['user_id']}")
    await message.answer(f"✅ {user['user_id']} bloklandi.", reply_markup=admin_menu())


@router.message(F.text == "✅ Unban")
async def start_unban(message: Message, state: FSMContext):
    await state.set_state(AdminUnbanStates.waiting_user)
    await message.answer(
        "✅ Blokdan chiqarmoqchi bo'lgan foydalanuvchi Telegram ID yoki Wallet ID sini kiriting:",
        reply_markup=cancel_keyboard(),
    )


@router.message(StateFilter(AdminUnbanStates.waiting_user))
async def process_unban(message: Message, state: FSMContext):
    query = message.text.strip().lstrip("@")
    user = await users_repo.get_user(int(query)) if query.isdigit() else await users_repo.get_user_by_wallet(query)
    await state.clear()

    if user is None:
        await message.answer("❌ Foydalanuvchi topilmadi.", reply_markup=admin_menu())
        return

    await users_repo.set_ban(user["user_id"], False)
    logger.info(f"Admin {message.from_user.id} userni blokdan chiqardi: {user['user_id']}")
    await message.answer(f"✅ {user['user_id']} blokdan chiqarildi.", reply_markup=admin_menu())
