from aiogram import Router, F
from aiogram.types import Message

from app.database import admins_repo
from app.keyboards.reply import admin_menu, main_menu

router = Router(name="help")


@router.message(F.text == "☎ Admin")
async def open_admin_menu(message: Message):
    if not await admins_repo.is_admin(message.from_user.id):
        await message.answer("Sizda ruxsat yo'q.")
        return
    await message.answer("⚙ Admin panelga xush kelibsiz.", reply_markup=admin_menu())


@router.message(F.text == "🔙 Bosh menu")
async def back_to_main_menu(message: Message):
    is_admin = await admins_repo.is_admin(message.from_user.id)
    await message.answer("🏠 Bosh menu", reply_markup=main_menu(is_admin=is_admin))
