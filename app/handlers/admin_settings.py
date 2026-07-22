from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.filters.admin import IsAdmin
from app.database import settings_repo
from app.keyboards.reply import cancel_keyboard, admin_menu
from app.states.states import AdminSetReferralBonusStates, AdminSetMinWithdrawStates

router = Router(name="admin_settings")
router.message.filter(IsAdmin())

CANCEL_TEXT = "🚫 Bekor qilish"


@router.message(F.text == "💎 Referral bonusini o'zgartirish")
async def start_set_referral_bonus(message: Message, state: FSMContext):
    current = await settings_repo.get_referral_bonus()
    await state.set_state(AdminSetReferralBonusStates.waiting_value)
    await message.answer(
        f"Joriy referral bonusi: {current} 💎\nYangi qiymatni kiriting:",
        reply_markup=cancel_keyboard(),
    )


@router.message(StateFilter(AdminSetReferralBonusStates.waiting_value), F.text == CANCEL_TEXT)
@router.message(StateFilter(AdminSetMinWithdrawStates.waiting_value), F.text == CANCEL_TEXT)
async def cancel_settings_change(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ Bekor qilindi.", reply_markup=admin_menu())


@router.message(StateFilter(AdminSetReferralBonusStates.waiting_value))
async def process_referral_bonus(message: Message, state: FSMContext):
    if not message.text.strip().isdigit():
        await message.answer("❌ Iltimos, faqat son kiriting.")
        return

    amount = int(message.text.strip())
    await settings_repo.set_referral_bonus(amount)
    await state.clear()
    await message.answer(f"✅ Referral bonusi {amount} 💎 ga o'zgartirildi.", reply_markup=admin_menu())


@router.message(F.text == "🎁 Minimal yechishni o'zgartirish")
async def start_set_min_withdraw(message: Message, state: FSMContext):
    current = await settings_repo.get_min_withdraw()
    await state.set_state(AdminSetMinWithdrawStates.waiting_value)
    await message.answer(
        f"Joriy minimal yechish miqdori: {current} 💎\nYangi qiymatni kiriting:",
        reply_markup=cancel_keyboard(),
    )


@router.message(StateFilter(AdminSetMinWithdrawStates.waiting_value))
async def process_min_withdraw(message: Message, state: FSMContext):
    if not message.text.strip().isdigit():
        await message.answer("❌ Iltimos, faqat son kiriting.")
        return

    amount = int(message.text.strip())
    await settings_repo.set_min_withdraw(amount)
    await state.clear()
    await message.answer(f"✅ Minimal yechish miqdori {amount} 💎 ga o'zgartirildi.", reply_markup=admin_menu())
