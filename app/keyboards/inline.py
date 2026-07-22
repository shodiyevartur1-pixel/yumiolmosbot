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