from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from app.filters.admin import IsAdmin
from app.database import settings_repo, packages_repo
from app.keyboards.reply import cancel_keyboard, admin_menu
from app.keyboards.inline import payment_settings_menu_keyboard, admin_packages_keyboard
from app.states.states import (
    AdminSetReferralBonusStates,
    AdminSetMinWithdrawStates,
    AdminPaymentSettingsStates,
    AdminPackageStates,
)

router = Router(name="admin_settings")
router.message.filter(IsAdmin())

CANCEL_TEXT = "🚫 Bekor qilish"


async def _payment_settings_text() -> str:
    card_owner = await settings_repo.get_card_owner()
    card_number = await settings_repo.get_card_number()
    payment_note = await settings_repo.get_payment_note()
    enabled = await settings_repo.get_payment_enabled()
    status = "🟢 Yoqilgan" if enabled else "🔴 O'chirilgan"
    return (
        "💳 <b>To'lov sozlamalari</b>\n\n"
        f"👤 Karta egasi: {card_owner}\n"
        f"💳 Karta raqami: <code>{card_number}</code>\n"
        f"📝 Eslatma: {payment_note}\n"
        f"⚙️ Holati: {status}\n\n"
        "Quyidagilardan birini tanlang:"
    )


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
@router.message(StateFilter(AdminPaymentSettingsStates.waiting_card_owner), F.text == CANCEL_TEXT)
@router.message(StateFilter(AdminPaymentSettingsStates.waiting_card_number), F.text == CANCEL_TEXT)
@router.message(StateFilter(AdminPaymentSettingsStates.waiting_payment_note), F.text == CANCEL_TEXT)
@router.message(StateFilter(AdminPackageStates.waiting_diamonds), F.text == CANCEL_TEXT)
@router.message(StateFilter(AdminPackageStates.waiting_price), F.text == CANCEL_TEXT)
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


# ===================== TO'LOV SOZLAMALARI =====================

@router.message(F.text == "💳 To'lov sozlamalari")
async def open_payment_settings(message: Message, state: FSMContext):
    await state.clear()
    enabled = await settings_repo.get_payment_enabled()
    await message.answer(
        await _payment_settings_text(),
        reply_markup=payment_settings_menu_keyboard(enabled),
    )


@router.callback_query(F.data == "pset_back")
async def pset_back(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    enabled = await settings_repo.get_payment_enabled()
    await callback.message.edit_text(
        await _payment_settings_text(),
        reply_markup=payment_settings_menu_keyboard(enabled),
    )
    await callback.answer()


@router.callback_query(F.data == "pset_toggle")
async def pset_toggle(callback: CallbackQuery):
    current = await settings_repo.get_payment_enabled()
    await settings_repo.set_payment_enabled(not current)
    enabled = not current
    await callback.message.edit_text(
        await _payment_settings_text(),
        reply_markup=payment_settings_menu_keyboard(enabled),
    )
    await callback.answer("🟢 Yoqildi." if enabled else "🔴 O'chirildi.")


@router.callback_query(F.data == "pset_owner")
async def pset_owner(callback: CallbackQuery, state: FSMContext):
    current = await settings_repo.get_card_owner()
    await state.set_state(AdminPaymentSettingsStates.waiting_card_owner)
    await callback.message.answer(
        f"Joriy karta egasi: <b>{current}</b>\nYangi ism va familiyani kiriting:",
        reply_markup=cancel_keyboard(),
    )
    await callback.answer()


@router.message(StateFilter(AdminPaymentSettingsStates.waiting_card_owner))
async def process_card_owner(message: Message, state: FSMContext):
    value = message.text.strip()
    if not value:
        await message.answer("❌ Bo'sh bo'lishi mumkin emas.")
        return
    await settings_repo.set_card_owner(value)
    await state.clear()
    await message.answer(f"✅ Karta egasi o'zgartirildi: {value}", reply_markup=admin_menu())


@router.callback_query(F.data == "pset_number")
async def pset_number(callback: CallbackQuery, state: FSMContext):
    current = await settings_repo.get_card_number()
    await state.set_state(AdminPaymentSettingsStates.waiting_card_number)
    await callback.message.answer(
        f"Joriy karta raqami: <code>{current}</code>\nYangi karta raqamini kiriting:",
        reply_markup=cancel_keyboard(),
    )
    await callback.answer()


@router.message(StateFilter(AdminPaymentSettingsStates.waiting_card_number))
async def process_card_number(message: Message, state: FSMContext):
    value = message.text.strip()
    if not value:
        await message.answer("❌ Bo'sh bo'lishi mumkin emas.")
        return
    await settings_repo.set_card_number(value)
    await state.clear()
    await message.answer(f"✅ Karta raqami o'zgartirildi: {value}", reply_markup=admin_menu())


@router.callback_query(F.data == "pset_note")
async def pset_note(callback: CallbackQuery, state: FSMContext):
    current = await settings_repo.get_payment_note()
    await state.set_state(AdminPaymentSettingsStates.waiting_payment_note)
    await callback.message.answer(
        f"Joriy eslatma matni:\n{current}\n\nYangi matnni kiriting:",
        reply_markup=cancel_keyboard(),
    )
    await callback.answer()


@router.message(StateFilter(AdminPaymentSettingsStates.waiting_payment_note))
async def process_payment_note(message: Message, state: FSMContext):
    value = message.text.strip()
    if not value:
        await message.answer("❌ Bo'sh bo'lishi mumkin emas.")
        return
    await settings_repo.set_payment_note(value)
    await state.clear()
    await message.answer("✅ Eslatma matni o'zgartirildi.", reply_markup=admin_menu())


# ===================== PAKETLARNI BOSHQARISH =====================

@router.callback_query(F.data == "pset_packages")
async def pset_packages(callback: CallbackQuery):
    packages = await packages_repo.get_all_packages()
    text = "📦 <b>Paketlar</b>\n\n" + (
        "Hozircha paketlar yo'q." if not packages else
        "🟢 - faol, 🔴 - nofaol. Holatini o'zgartirish uchun ustiga bosing."
    )
    await callback.message.edit_text(text, reply_markup=admin_packages_keyboard(packages))
    await callback.answer()


@router.callback_query(F.data.startswith("pkg_toggle:"))
async def pkg_toggle(callback: CallbackQuery):
    package_id = int(callback.data.split(":")[1])
    package = await packages_repo.get_package(package_id)
    if package is None:
        await callback.answer("Paket topilmadi.", show_alert=True)
        return
    await packages_repo.set_active(package_id, not package["is_active"])
    packages = await packages_repo.get_all_packages()
    text = "📦 <b>Paketlar</b>\n\n🟢 - faol, 🔴 - nofaol. Holatini o'zgartirish uchun ustiga bosing."
    await callback.message.edit_text(text, reply_markup=admin_packages_keyboard(packages))
    await callback.answer()


@router.callback_query(F.data.startswith("pkg_delete:"))
async def pkg_delete(callback: CallbackQuery):
    package_id = int(callback.data.split(":")[1])
    await packages_repo.remove_package(package_id)
    packages = await packages_repo.get_all_packages()
    text = "📦 <b>Paketlar</b>\n\n" + (
        "Hozircha paketlar yo'q." if not packages else
        "🟢 - faol, 🔴 - nofaol. Holatini o'zgartirish uchun ustiga bosing."
    )
    await callback.message.edit_text(text, reply_markup=admin_packages_keyboard(packages))
    await callback.answer("🗑 Paket o'chirildi.")


@router.callback_query(F.data == "pkg_add")
async def pkg_add(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AdminPackageStates.waiting_diamonds)
    await callback.message.answer(
        "💎 Nechta Almazdan iborat paket qo'shmoqchisiz? (masalan: 1000)",
        reply_markup=cancel_keyboard(),
    )
    await callback.answer()


@router.message(StateFilter(AdminPackageStates.waiting_diamonds))
async def process_pkg_diamonds(message: Message, state: FSMContext):
    if not message.text.strip().isdigit():
        await message.answer("❌ Iltimos, faqat son kiriting.")
        return
    await state.update_data(diamonds=int(message.text.strip()))
    await state.set_state(AdminPackageStates.waiting_price)
    await message.answer("💰 Paket narxini so'mda kiriting (masalan: 4500):")


@router.message(StateFilter(AdminPackageStates.waiting_price))
async def process_pkg_price(message: Message, state: FSMContext):
    if not message.text.strip().isdigit():
        await message.answer("❌ Iltimos, faqat son kiriting.")
        return

    data = await state.get_data()
    diamonds = data["diamonds"]
    price = int(message.text.strip())
    await packages_repo.add_package(diamonds, price)
    await state.clear()

    await message.answer(
        f"✅ Yangi paket qo'shildi: {diamonds} 💎 — {price:,} so'm".replace(",", " "),
        reply_markup=admin_menu(),
    )
