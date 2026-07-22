"""
/start handleri:
1. Majburiy kanal a'zoligini tekshiradi
2. A'zo bo'lmasa - obuna bo'lish tugmalarini ko'rsatadi
3. A'zo bo'lsa - ro'yxatdan o'tkazadi (agar hali o'tmagan bo'lsa) va
   referral bonusini hisoblaydi
"""
from aiogram import Router, F
from aiogram.filters import CommandStart, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from app.database import users_repo, channels_repo, referrals_repo, settings_repo, admins_repo
from app.keyboards.inline import subscription_keyboard
from app.keyboards.reply import main_menu
from app.services.subscription import get_not_subscribed_channels
from app.utils.logger import logger

router = Router(name="start")


def _extract_referrer_id(command: CommandObject) -> int | None:
    if not command.args:
        return None
    arg = command.args.strip()
    if arg.isdigit():
        return int(arg)
    return None


async def _valid_referrer(referrer_id: int | None, user_id: int) -> int | None:
    if not referrer_id or referrer_id == user_id:
        return None
    if await users_repo.user_exists(referrer_id):
        return referrer_id
    return None


async def _notify_referrer_pending(bot, user, referrer_id: int | None, state: FSMContext) -> None:
    """
    Foydalanuvchi referal havola orqali kirdi, lekin hali majburiy
    kanallarga to'liq a'zo bo'lmadi - referrer'ga bir martalik
    ogohlantirish yuboradi.
    """
    user_id = user.id
    if await users_repo.user_exists(user_id):
        return  # allaqachon ro'yxatdan o'tgan, bu yangi referal emas

    valid_referrer = await _valid_referrer(referrer_id, user_id)
    if valid_referrer is None:
        return

    data = await state.get_data()
    if data.get("referrer_pending_notified"):
        return

    invited_name = user.first_name or (f"@{user.username}" if user.username else f"ID{user_id}")
    try:
        await bot.send_message(
            valid_referrer,
            f"👀 <b>{invited_name}</b> sizning referal havolangiz orqali botga kirdi, "
            "lekin hali majburiy kanallarga to'liq a'zo bo'lmadi.\n"
            "A'zo bo'lgach, sizga avtomatik ravishda bonus qo'shiladi.",
        )
    except Exception:
        pass

    await state.update_data(referrer_pending_notified=True)


async def _send_subscription_prompt(message_or_callback, not_subscribed) -> None:
    text = "❌ Botdan foydalanish uchun quyidagi kanallarga obuna bo'ling."
    keyboard = subscription_keyboard(not_subscribed)
    if isinstance(message_or_callback, CallbackQuery):
        await message_or_callback.message.edit_text(text, reply_markup=keyboard)
    else:
        await message_or_callback.answer(text, reply_markup=keyboard)


async def _finish_registration(message: Message, referrer_id: int | None):
    user_id = message.from_user.id
    is_new = not await users_repo.user_exists(user_id)

    if is_new:
        valid_referrer = await _valid_referrer(referrer_id, user_id)

        await users_repo.create_user(
            user_id=user_id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            referred_by=valid_referrer,
        )

        if valid_referrer:
            bonus = await settings_repo.get_referral_bonus()
            await referrals_repo.register_referral(valid_referrer, user_id, bonus)

            invited_name = message.from_user.first_name or (
                f"@{message.from_user.username}" if message.from_user.username else f"ID{user_id}"
            )
            try:
                await message.bot.send_message(
                    valid_referrer,
                    f"🎉 <b>{invited_name}</b> sizning referal havolangiz orqali botga qo'shildi!\n"
                    f"💎 Balansingizga {bonus} Yumi Almaz qo'shildi.",
                )
            except Exception:
                pass
    else:
        await users_repo.update_username(
            user_id, message.from_user.username, message.from_user.first_name
        )

    is_admin = await admins_repo.is_admin(user_id)
    await message.answer(
        "🎉 Xush kelibsiz, Yumi Almaz botiga!\n\n"
        "Bu yerda siz do'stlaringizni taklif qilib Yumi Almaz yig'ishingiz "
        "va yechib olishingiz mumkin.\n\n"
        "Quyidagi menyudan kerakli bo'limni tanlang 👇",
        reply_markup=main_menu(is_admin=is_admin),
    )


@router.message(CommandStart())
async def cmd_start(message: Message, command: CommandObject, state: FSMContext):
    referrer_id = _extract_referrer_id(command)
    if referrer_id is not None:
        await state.update_data(pending_referrer_id=referrer_id)
    else:
        # Foydalanuvchi avval referal havola orqali kirib, obunani
        # "Tekshirish" tugmasisiz, oddiy /start orqali yakunlagan bo'lishi
        # mumkin - bu holda oldin saqlangan referrer_id'ni tiklaymiz.
        data = await state.get_data()
        referrer_id = data.get("pending_referrer_id")

    not_subscribed = await get_not_subscribed_channels(message.bot, message.from_user.id)

    if not_subscribed:
        await _notify_referrer_pending(message.bot, message.from_user, referrer_id, state)
        await _send_subscription_prompt(message, not_subscribed)
        return

    await _finish_registration(message, referrer_id)


@router.callback_query(F.data == "check_subscription")
async def check_subscription_callback(callback: CallbackQuery, state: FSMContext):
    not_subscribed = await get_not_subscribed_channels(callback.bot, callback.from_user.id)

    if not_subscribed:
        data = await state.get_data()
        referrer_id = data.get("pending_referrer_id")
        await _notify_referrer_pending(callback.bot, callback.from_user, referrer_id, state)
        await callback.answer("❌ Siz hali barcha kanallarga a'zo bo'lmagansiz.", show_alert=True)
        await _send_subscription_prompt(callback, not_subscribed)
        return

    data = await state.get_data()
    referrer_id = data.get("pending_referrer_id")

    await callback.answer("✅ Tabriklaymiz!")
    await callback.message.delete()
    await _finish_registration(callback.message, referrer_id=referrer_id)
    await state.update_data(pending_referrer_id=None)