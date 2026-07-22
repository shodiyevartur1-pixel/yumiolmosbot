from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from app.database import users_repo, settings_repo, withdraws_repo, admins_repo
from app.keyboards.reply import main_menu, cancel_keyboard
from app.keyboards.inline import withdraw_confirm_keyboard, withdraw_admin_keyboard
from app.states.states import WithdrawStates
from app.utils.logger import logger

router = Router(name="withdraw")


async def _main_menu_for(user_id: int):
    is_admin = await admins_repo.is_admin(user_id)
    return main_menu(is_admin=is_admin)

CANCEL_TEXT = "🚫 Bekor qilish"


@router.message(F.text == "🎁 Almazni yechish")
async def start_withdraw(message: Message, state: FSMContext):
    user = await users_repo.get_user(message.from_user.id)
    if user is None:
        await message.answer("Iltimos, avval /start buyrug'ini bosing.")
        return

    min_withdraw = await settings_repo.get_min_withdraw()
    if user["balance"] < min_withdraw:
        await message.answer(
            f"❌ Yechish uchun minimal miqdor {min_withdraw} 💎.\n"
            f"Sizning balansingiz: {user['balance']} 💎"
        )
        return

    await state.set_state(WithdrawStates.waiting_game_id)
    await message.answer("🎮 Yumicoin ID kiriting:", reply_markup=cancel_keyboard())


@router.message(StateFilter(WithdrawStates.waiting_game_id), F.text == CANCEL_TEXT)
@router.message(StateFilter(WithdrawStates.waiting_amount), F.text == CANCEL_TEXT)
@router.message(StateFilter(WithdrawStates.confirm), F.text == CANCEL_TEXT)
async def cancel_withdraw(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ Bekor qilindi.", reply_markup=await _main_menu_for(message.from_user.id))


@router.message(StateFilter(WithdrawStates.waiting_game_id))
async def process_game_id(message: Message, state: FSMContext):
    game_id = message.text.strip()
    if not game_id:
        await message.answer("❌ Game ID bo'sh bo'lishi mumkin emas.")
        return

    await state.update_data(game_id=game_id)
    await state.set_state(WithdrawStates.waiting_amount)
    await message.answer("💎 Nechta Yumi Almaz yechmoqchisiz?")


@router.message(StateFilter(WithdrawStates.waiting_amount))
async def process_withdraw_amount(message: Message, state: FSMContext):
    if not message.text.strip().isdigit():
        await message.answer("❌ Iltimos, faqat son kiriting.")
        return

    amount = int(message.text.strip())
    min_withdraw = await settings_repo.get_min_withdraw()

    if amount < min_withdraw:
        await message.answer(f"❌ Minimal yechish miqdori {min_withdraw} 💎.")
        return

    user = await users_repo.get_user(message.from_user.id)
    if amount > user["balance"]:
        await message.answer(f"❌ Balansingiz yetarli emas. Joriy balans: {user['balance']} 💎")
        return

    data = await state.get_data()
    game_id = data["game_id"]
    await state.update_data(amount=amount)
    await state.set_state(WithdrawStates.confirm)

    await message.answer(
        f"📝 <b>So'rovni tasdiqlang</b>\n\n"
        f"Yumicoin ID: <code>{game_id}</code>\n"
        f"Miqdor: {amount} 💎\n\n"
        "Ma'lumotlar to'g'rimi?",
        reply_markup=withdraw_confirm_keyboard(),
    )


@router.callback_query(StateFilter(WithdrawStates.confirm), F.data == "withdraw_confirm")
async def confirm_withdraw(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    game_id = data["game_id"]
    amount = data["amount"]

    user = await users_repo.get_user(callback.from_user.id)
    if amount > user["balance"]:
        await callback.message.edit_text("❌ Balansingiz yetarli emas.")
        await state.clear()
        await callback.answer()
        await callback.message.answer(
            "Bosh menu:", reply_markup=await _main_menu_for(callback.from_user.id)
        )
        return

    withdraw_id = await withdraws_repo.create_withdraw_request(
        callback.from_user.id, game_id, amount
    )
    await state.clear()

    await callback.message.edit_text(
        "✅ So'rovingiz yuborildi. Admin tasdiqlashini kuting."
    )
    await callback.answer()
    await callback.message.answer(
        "Bosh menu:", reply_markup=await _main_menu_for(callback.from_user.id)
    )

    admin_text = (
        "🆕 <b>Yangi yechish so'rovi</b>\n\n"
        f"Foydalanuvchi: {user['first_name'] or '-'} "
        f"({'@' + user['username'] if user['username'] else user['user_id']})\n"
        f"Yumicoin ID: <code>{game_id}</code>\n"
        f"Miqdor: {amount} 💎"
    )
    for admin_id in await admins_repo.get_all_admins():
        try:
            await callback.bot.send_message(
                admin_id, admin_text, reply_markup=withdraw_admin_keyboard(withdraw_id)
            )
        except Exception as e:
            logger.warning(f"Adminga xabar yuborib bo'lmadi {admin_id}: {e}")


@router.callback_query(StateFilter(WithdrawStates.confirm), F.data == "withdraw_cancel")
async def cancel_withdraw_callback(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Bekor qilindi.")
    await callback.answer()
    await callback.message.answer(
        "Bosh menu:", reply_markup=await _main_menu_for(callback.from_user.id)
    )


@router.callback_query(F.data.startswith("wd_approve:"))
async def approve_withdraw_callback(callback: CallbackQuery):
    if not await admins_repo.is_admin(callback.from_user.id):
        await callback.answer("Sizda ruxsat yo'q.", show_alert=True)
        return

    withdraw_id = int(callback.data.split(":")[1])
    success, msg = await withdraws_repo.approve_withdraw(withdraw_id, callback.from_user.id)

    await callback.answer(msg, show_alert=not success)
    if success:
        withdraw = await withdraws_repo.get_withdraw(withdraw_id)
        await callback.message.edit_text(callback.message.text + "\n\n✅ Tasdiqlandi.")
        try:
            await callback.bot.send_message(
                withdraw["user_id"], "✅ So'rovingiz tasdiqlandi Olmos yumicoin hisobingizga yuborildi.",
            )
        except Exception:
            pass


@router.callback_query(F.data.startswith("wd_reject:"))
async def reject_withdraw_callback(callback: CallbackQuery):
    if not await admins_repo.is_admin(callback.from_user.id):
        await callback.answer("Sizda ruxsat yo'q.", show_alert=True)
        return

    withdraw_id = int(callback.data.split(":")[1])
    success, msg = await withdraws_repo.reject_withdraw(withdraw_id, callback.from_user.id)

    await callback.answer(msg, show_alert=not success)
    if success:
        withdraw = await withdraws_repo.get_withdraw(withdraw_id)
        await callback.message.edit_text(callback.message.text + "\n\n❌ Bekor qilindi.")
        try:
            await callback.bot.send_message(
                withdraw["user_id"], "❌ Bekor qilindi."
            )
        except Exception:
            pass