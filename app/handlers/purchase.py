from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from app.database import (
    users_repo,
    settings_repo,
    packages_repo,
    purchases_repo,
    admins_repo,
)
from app.keyboards.reply import main_menu
from app.keyboards.inline import (
    packages_keyboard,
    payment_page_keyboard,
    purchase_admin_keyboard,
)
from app.states.states import PurchaseStates
from app.utils.logger import logger

router = Router(name="purchase")

CANCEL_TEXT = "🚫 Bekor qilish"


async def _main_menu_for(user_id: int):
    is_admin = await admins_repo.is_admin(user_id)
    return main_menu(is_admin=is_admin)


@router.message(F.text == "🛒 Almaz sotib olish")
async def start_purchase(message: Message, state: FSMContext):
    user = await users_repo.get_user(message.from_user.id)
    if user is None:
        await message.answer("Iltimos, avval /start buyrug'ini bosing.")
        return

    if not await settings_repo.get_payment_enabled():
        await message.answer("⚠️ Hozircha to'lov tizimi vaqtincha o'chirilgan. Keyinroq urinib ko'ring.")
        return

    packages = await packages_repo.get_all_packages(active_only=True)
    if not packages:
        await message.answer("⚠️ Hozircha sotuvda paketlar mavjud emas. Keyinroq urinib ko'ring.")
        return

    await state.clear()
    await message.answer(
        "💎 <b>Almaz sotib olish</b>\n\nQuyidagi paketlardan birini tanlang:",
        reply_markup=packages_keyboard(packages),
    )


@router.callback_query(F.data.startswith("buy_pkg:"))
async def choose_package(callback: CallbackQuery, state: FSMContext):
    package_id = int(callback.data.split(":")[1])
    package = await packages_repo.get_package(package_id)
    if package is None or not package["is_active"]:
        await callback.answer("Bu paket endi mavjud emas.", show_alert=True)
        return

    card_owner = await settings_repo.get_card_owner()
    card_number = await settings_repo.get_card_number()
    payment_note = await settings_repo.get_payment_note()

    text = (
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "💎 <b>Almaz sotib olish</b>\n\n"
        f"📦 Paket: {package['diamonds']} Almaz\n"
        f"💰 Narxi: {package['price']:,} so'm\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "💳 <b>To'lov kartasi</b>\n\n"
        f"👤 Karta egasi: {card_owner}\n"
        f"💳 Karta raqami: <code>{card_number}</code>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"⚠️ <b>Eslatma</b>\n{payment_note}\n"
        "━━━━━━━━━━━━━━━━━━━━━━"
    ).replace(",", " ")

    await callback.message.edit_text(text, reply_markup=payment_page_keyboard(card_number, package_id))
    await callback.answer()


@router.callback_query(F.data == "buy_cancel")
async def cancel_purchase_callback(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Almaz sotib olish bekor qilindi.")
    await callback.answer()
    await callback.message.answer(
        "Bosh menu:", reply_markup=await _main_menu_for(callback.from_user.id)
    )


@router.callback_query(F.data.startswith("buy_paid:"))
async def ask_receipt(callback: CallbackQuery, state: FSMContext):
    package_id = int(callback.data.split(":")[1])
    package = await packages_repo.get_package(package_id)
    if package is None or not package["is_active"]:
        await callback.answer("Bu paket endi mavjud emas.", show_alert=True)
        return

    await state.set_state(PurchaseStates.waiting_receipt)
    await state.update_data(package_id=package_id)

    await callback.message.edit_text(
        "📸 To'lov chekini (screenshot yoki rasm) yuboring."
    )
    await callback.answer()


@router.message(StateFilter(PurchaseStates.waiting_receipt), F.text == CANCEL_TEXT)
async def cancel_receipt_wait(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ Bekor qilindi.", reply_markup=await _main_menu_for(message.from_user.id))


@router.message(StateFilter(PurchaseStates.waiting_receipt), F.photo)
async def process_receipt(message: Message, state: FSMContext):
    data = await state.get_data()
    package_id = data.get("package_id")
    package = await packages_repo.get_package(package_id)
    if package is None:
        await state.clear()
        await message.answer(
            "❌ Bu paket endi mavjud emas. Iltimos, qaytadan urinib ko'ring.",
            reply_markup=await _main_menu_for(message.from_user.id),
        )
        return

    user = await users_repo.get_user(message.from_user.id)
    receipt_file_id = message.photo[-1].file_id

    purchase_id = await purchases_repo.create_purchase(
        user_id=message.from_user.id,
        package_id=package["id"],
        diamonds=package["diamonds"],
        price=package["price"],
        receipt_file_id=receipt_file_id,
    )
    await state.clear()

    await message.answer(
        "⏳ Chekingiz qabul qilindi. Admin tasdiqlashini kuting.",
        reply_markup=await _main_menu_for(message.from_user.id),
    )

    username_line = f"@{user['username']}" if user and user["username"] else "-"
    card_number = await settings_repo.get_card_number()

    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)

    admin_text = (
        "🆕 <b>Yangi Almaz xaridi</b>\n\n"
        f"👤 Ism: {user['first_name'] or '-'}\n"
        f"🆔 Telegram ID: <code>{message.from_user.id}</code>\n"
        f"🆔 Username: {username_line}\n"
        f"💎 Paket: {package['diamonds']} Almaz\n"
        f"💰 Narxi: {package['price']:,} so'm\n"
        f"💳 To'lov kartasi: {card_number}\n"
        f"📅 Sana: {now.strftime('%d.%m.%Y')}\n"
        f"🕒 Vaqt: {now.strftime('%H:%M')}"
    ).replace(",", " ")

    for admin_id in await admins_repo.get_all_admins():
        try:
            await message.bot.send_photo(
                admin_id,
                photo=receipt_file_id,
                caption=admin_text,
                reply_markup=purchase_admin_keyboard(purchase_id),
            )
        except Exception as e:
            logger.warning(f"Adminga chek yuborib bo'lmadi {admin_id}: {e}")


@router.message(StateFilter(PurchaseStates.waiting_receipt))
async def receipt_wrong_type(message: Message):
    await message.answer("📸 Iltimos, to'lov chekini rasm (screenshot) shaklida yuboring.")


@router.callback_query(F.data.startswith("pur_approve:"))
async def approve_purchase_callback(callback: CallbackQuery):
    if not await admins_repo.is_admin(callback.from_user.id):
        await callback.answer("Sizda ruxsat yo'q.", show_alert=True)
        return

    purchase_id = int(callback.data.split(":")[1])
    success, msg = await purchases_repo.approve_purchase(purchase_id, callback.from_user.id)
    await callback.answer(msg, show_alert=not success)
    if not success:
        return

    purchase = await purchases_repo.get_purchase(purchase_id)
    await callback.message.edit_caption(
        caption=(callback.message.caption or "") + "\n\n✅ Tasdiqlandi.",
        reply_markup=None,
    )
    try:
        await callback.bot.send_message(
            purchase["user_id"],
            "🎉 To'lovingiz muvaffaqiyatli tasdiqlandi!\n"
            f"💎 {purchase['diamonds']} Almaz hisobingizga qo'shildi.\n\n"
            "Yaxshi xaridlar tilaymiz! ❤️",
        )
    except Exception as e:
        logger.warning(f"Foydalanuvchiga xabar yuborib bo'lmadi {purchase['user_id']}: {e}")


@router.callback_query(F.data.startswith("pur_reject:"))
async def reject_purchase_callback(callback: CallbackQuery):
    if not await admins_repo.is_admin(callback.from_user.id):
        await callback.answer("Sizda ruxsat yo'q.", show_alert=True)
        return

    purchase_id = int(callback.data.split(":")[1])
    success, msg = await purchases_repo.reject_purchase(purchase_id, callback.from_user.id)
    await callback.answer(msg, show_alert=not success)
    if not success:
        return

    purchase = await purchases_repo.get_purchase(purchase_id)
    await callback.message.edit_caption(
        caption=(callback.message.caption or "") + "\n\n❌ Rad etildi.",
        reply_markup=None,
    )
    try:
        await callback.bot.send_message(
            purchase["user_id"],
            "❌ To'lovingiz rad etildi.\n\n"
            "Iltimos, to'g'ri chek yuborib qayta urinib ko'ring.",
        )
    except Exception as e:
        logger.warning(f"Foydalanuvchiga xabar yuborib bo'lmadi {purchase['user_id']}: {e}")
