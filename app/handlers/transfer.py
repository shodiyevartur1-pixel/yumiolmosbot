from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from app.database import users_repo, admins_repo
from app.database.transfers_repo import transfer, TransferResult
from app.keyboards.reply import main_menu, cancel_keyboard
from app.keyboards.inline import transfer_confirm_keyboard
from app.states.states import TransferStates

router = Router(name="transfer")

CANCEL_TEXT = "🚫 Bekor qilish"


@router.message(F.text == "💸 Almaz yuborish")
async def start_transfer(message: Message, state: FSMContext):
    user = await users_repo.get_user(message.from_user.id)
    if user is None:
        await message.answer("Iltimos, avval /start buyrug'ini bosing.")
        return

    await state.set_state(TransferStates.waiting_wallet_id)
    await message.answer(
        "💳 Qabul qiluvchining Wallet ID sini kiriting.\n"
        "Masalan: <code>MK7T3</code>",
        reply_markup=cancel_keyboard(),
    )


@router.message(StateFilter(TransferStates.waiting_wallet_id), F.text == CANCEL_TEXT)
@router.message(StateFilter(TransferStates.waiting_amount), F.text == CANCEL_TEXT)
async def cancel_transfer(message: Message, state: FSMContext):
    await state.clear()
    is_admin = await admins_repo.is_admin(message.from_user.id)
    await message.answer("❌ Bekor qilindi.", reply_markup=main_menu(is_admin=is_admin))


@router.message(StateFilter(TransferStates.waiting_wallet_id))
async def process_wallet_id(message: Message, state: FSMContext):
    wallet_id = message.text.strip().upper()

    receiver = await users_repo.get_user_by_wallet(wallet_id)
    if receiver is None:
        await message.answer("❌ Bunday Wallet ID topilmadi. Qaytadan kiriting.")
        return

    if receiver["user_id"] == message.from_user.id:
        await message.answer("❌ O'zingizga o'tkazma qila olmaysiz. Boshqa Wallet ID kiriting.")
        return

    await state.update_data(wallet_id=wallet_id)
    await state.set_state(TransferStates.waiting_amount)
    await message.answer("💎 Nechta Yumi Almaz yubormoqchisiz?")


@router.message(StateFilter(TransferStates.waiting_amount))
async def process_amount(message: Message, state: FSMContext):
    if not message.text.strip().isdigit():
        await message.answer("❌ Iltimos, faqat son kiriting.")
        return

    amount = int(message.text.strip())
    if amount <= 0:
        await message.answer("❌ Miqdor musbat bo'lishi kerak.")
        return

    user = await users_repo.get_user(message.from_user.id)
    if amount > user["balance"]:
        await message.answer(f"❌ Balansingiz yetarli emas. Joriy balans: {user['balance']} 💎")
        return

    data = await state.get_data()
    wallet_id = data["wallet_id"]
    await state.update_data(amount=amount)
    await state.set_state(TransferStates.confirm)

    await message.answer(
        f"📤 <b>Tasdiqlang</b>\n\n"
        f"Qabul qiluvchi: <code>{wallet_id}</code>\n"
        f"Miqdor: {amount} 💎\n\n"
        "Ma'lumotlar to'g'rimi?",
        reply_markup=transfer_confirm_keyboard(),
    )


@router.callback_query(StateFilter(TransferStates.confirm), F.data == "transfer_confirm")
async def confirm_transfer(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    wallet_id = data["wallet_id"]
    amount = data["amount"]

    result, receiver = await transfer(callback.from_user.id, wallet_id, amount)

    if result == TransferResult.OK:
        text = f"✅ {amount} 💎 muvaffaqiyatli yuborildi.\nQabul qiluvchi: {wallet_id}"
        try:
            await callback.bot.send_message(
                receiver["user_id"],
                f"💎 Sizga {amount} Yumi Almaz kelib tushdi!",
            )
        except Exception:
            pass
    elif result == TransferResult.NOT_FOUND:
        text = "❌ Qabul qiluvchi topilmadi."
    elif result == TransferResult.SELF:
        text = "❌ O'zingizga o'tkazma qila olmaysiz."
    elif result == TransferResult.INSUFFICIENT:
        text = "❌ Balansingiz yetarli emas."
    elif result == TransferResult.BANNED:
        text = "❌ Bu foydalanuvchi bloklangan."
    else:
        text = "❌ Xatolik yuz berdi."

    await state.clear()
    await callback.message.edit_text(text)
    await callback.answer()


@router.callback_query(StateFilter(TransferStates.confirm), F.data == "transfer_cancel")
async def cancel_transfer_callback(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Bekor qilindi.")
    await callback.answer()