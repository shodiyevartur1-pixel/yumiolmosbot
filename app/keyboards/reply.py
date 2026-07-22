from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

MAIN_MENU_BUTTONS = {
    "profile": "👤 Profil",
    "referral": "👥 Referal",
    "balance": "💎 Balans",
    "withdraw": "🎁 Almazni yechish",
    "history": "📜 Tarix",
    "admin": "☎ Admin",
}


def main_menu(is_admin: bool = False) -> ReplyKeyboardMarkup:
    rows = [
        [KeyboardButton(text=MAIN_MENU_BUTTONS["profile"]), KeyboardButton(text=MAIN_MENU_BUTTONS["referral"])],
        [KeyboardButton(text=MAIN_MENU_BUTTONS["balance"]), KeyboardButton(text=MAIN_MENU_BUTTONS["withdraw"])],
        [KeyboardButton(text=MAIN_MENU_BUTTONS["history"])],
    ]
    if is_admin:
        rows.append([KeyboardButton(text=MAIN_MENU_BUTTONS["admin"])])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


def cancel_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="🚫 Bekor qilish")]],
        resize_keyboard=True,
    )


ADMIN_MENU_BUTTONS = [
    "👤 Statistika",
    "📢 Reklama yuborish",
    "📊 Referral statistikasi",
    "➕ Kanal qo'shish",
    "➖ Kanal o'chirish",
    "✏ Kanal usernameni o'zgartirish",
    "💎 Referral bonusini o'zgartirish",
    "🎁 Minimal yechishni o'zgartirish",
    "➕ Userga almaz qo'shish",
    "➖ Userdan almaz ayirish",
    "🔍 User qidirish",
    "🚫 Ban",
    "✅ Unban",
    "📜 Withdrawal history",
    "📦 Transfer history",
    "📈 Aktiv userlar",
    "📅 Bugungi userlar",
    "♻ Restart",
    "🔙 Bosh menu",
]


def admin_menu() -> ReplyKeyboardMarkup:
    rows = [ADMIN_MENU_BUTTONS[i:i + 2] for i in range(0, len(ADMIN_MENU_BUTTONS), 2)]
    keyboard = [[KeyboardButton(text=t) for t in row] for row in rows]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)
