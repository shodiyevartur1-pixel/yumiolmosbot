from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CopyTextButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def subscription_keyboard(channels) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for ch in channels:
        invite_link = ch["invite_link"] if "invite_link" in ch.keys() else None
        username = ch["username"]

        if invite_link:
            url = invite_link
        elif username:
            url = f"https://t.me/{username.lstrip('@')}"
        else:
            continue  # na username, na invite_link - tugma yasab bo'lmaydi

        label = ch["title"] or (f"@{username}" if username else "Kanal")
        builder.row(InlineKeyboardButton(text=f"📢 {label}", url=url))
    builder.row(InlineKeyboardButton(text="✅ Tekshirish", callback_data="check_subscription"))
    return builder.as_markup()


def referral_link_keyboard(ref_link: str) -> InlineKeyboardMarkup:
    """
    Referal havolasini bitta bosishda nusxalash uchun tugma.
    Telegram'ning native "copy_text" tugmasidan foydalanadi - bosilganda
    havola avtomatik ravishda foydalanuvchi clipboard'iga nusxalanadi.
    """
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="📋 Havolani nusxalash",
            copy_text=CopyTextButton(text=ref_link),
        )
    )
    return builder.as_markup()


def transfer_confirm_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ Tasdiqlash", callback_data="transfer_confirm"),
        InlineKeyboardButton(text="❌ Bekor qilish", callback_data="transfer_cancel"),
    )
    return builder.as_markup()


def withdraw_confirm_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ Tasdiqlash", callback_data="withdraw_confirm"),
        InlineKeyboardButton(text="❌ Bekor qilish", callback_data="withdraw_cancel"),
    )
    return builder.as_markup()


def withdraw_admin_keyboard(withdraw_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"wd_approve:{withdraw_id}"),
        InlineKeyboardButton(text="❌ Bekor qilish", callback_data=f"wd_reject:{withdraw_id}"),
    )
    return builder.as_markup()


def broadcast_confirm_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ Yuborish", callback_data="broadcast_confirm"),
        InlineKeyboardButton(text="❌ Bekor qilish", callback_data="broadcast_cancel"),
    )
    return builder.as_markup()


def packages_keyboard(packages) -> InlineKeyboardMarkup:
    """Foydalanuvchi uchun Almaz paketlari ro'yxati."""
    builder = InlineKeyboardBuilder()
    for pkg in packages:
        builder.row(
            InlineKeyboardButton(
                text=f"💎 {pkg['diamonds']} Almaz — {pkg['price']:,} so'm".replace(",", " "),
                callback_data=f"buy_pkg:{pkg['id']}",
            )
        )
    builder.row(InlineKeyboardButton(text="❌ Bekor qilish", callback_data="buy_cancel"))
    return builder.as_markup()


def payment_page_keyboard(card_number: str, package_id: int) -> InlineKeyboardMarkup:
    """Karta raqamini nusxalash + To'lov qildim + Bekor qilish tugmalari."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="📋 Karta raqamini nusxalash",
            copy_text=CopyTextButton(text=card_number.replace(" ", "")),
        )
    )
    builder.row(InlineKeyboardButton(text="✅ To'lov qildim", callback_data=f"buy_paid:{package_id}"))
    builder.row(InlineKeyboardButton(text="❌ Bekor qilish", callback_data="buy_cancel"))
    return builder.as_markup()


def purchase_admin_keyboard(purchase_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"pur_approve:{purchase_id}"),
        InlineKeyboardButton(text="❌ Rad etish", callback_data=f"pur_reject:{purchase_id}"),
    )
    return builder.as_markup()


def payment_settings_menu_keyboard(payment_enabled: bool) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="👤 Karta egasini o'zgartirish", callback_data="pset_owner"))
    builder.row(InlineKeyboardButton(text="💳 Karta raqamini o'zgartirish", callback_data="pset_number"))
    builder.row(InlineKeyboardButton(text="📝 Eslatma matnini o'zgartirish", callback_data="pset_note"))
    builder.row(InlineKeyboardButton(text="📦 Paketlarni boshqarish", callback_data="pset_packages"))
    toggle_text = "🔴 To'lovni o'chirish" if payment_enabled else "🟢 To'lovni yoqish"
    builder.row(InlineKeyboardButton(text=toggle_text, callback_data="pset_toggle"))
    return builder.as_markup()


def admin_packages_keyboard(packages) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for pkg in packages:
        status = "🟢" if pkg["is_active"] else "🔴"
        builder.row(
            InlineKeyboardButton(
                text=f"{status} {pkg['diamonds']} 💎 — {pkg['price']:,} so'm".replace(",", " "),
                callback_data=f"pkg_toggle:{pkg['id']}",
            ),
            InlineKeyboardButton(text="🗑", callback_data=f"pkg_delete:{pkg['id']}"),
        )
    builder.row(InlineKeyboardButton(text="➕ Yangi paket qo'shish", callback_data="pkg_add"))
    builder.row(InlineKeyboardButton(text="⬅️ Orqaga", callback_data="pset_back"))
    return builder.as_markup()


def channels_list_keyboard(channels, callback_prefix: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for ch in channels:
        label = f"@{ch['username']}" if ch["username"] else (ch["title"] or f"ID{ch['id']}")
        builder.row(
            InlineKeyboardButton(
                text=label, callback_data=f"{callback_prefix}:{ch['id']}"
            )
        )
    return builder.as_markup()