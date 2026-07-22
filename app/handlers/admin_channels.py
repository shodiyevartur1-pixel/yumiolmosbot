import re

from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from app.filters.admin import IsAdmin
from app.database import channels_repo
from app.keyboards.reply import cancel_keyboard, admin_menu
from app.keyboards.inline import channels_list_keyboard
from app.states.states import AdminAddChannelStates, AdminRemoveChannelStates, AdminChangeChannelStates
from app.utils.logger import logger

router = Router(name="admin_channels")
router.message.filter(IsAdmin())

CANCEL_TEXT = "🚫 Bekor qilish"
WAITING_FORWARD_STATE = "admin_channels:waiting_forward"

PRIVATE_LINK_RE = re.compile(r"(?:t\.me/(?:\+|joinchat/))([A-Za-z0-9_-]+)")
PUBLIC_LINK_RE = re.compile(r"t\.me/([A-Za-z0-9_]+)")


@router.message(F.text == "➕ Kanal qo'shish")
async def start_add_channel(message: Message, state: FSMContext):
    await state.set_state(AdminAddChannelStates.waiting_username)
    await message.answer(
        "📢 Kanalni yuboring - quyidagilardan biri bo'lishi mumkin:\n\n"
        "• Username: @mychannel\n"
        "• Ochiq kanal linki: https://t.me/mychannel\n"
        "• Yopiq kanal (invite) linki: https://t.me/+xxxxxxxx\n\n"
        "Eslatma: bot kanalda admin bo'lishi shart.",
        reply_markup=cancel_keyboard(),
    )


@router.message(StateFilter(AdminAddChannelStates.waiting_username), F.text == CANCEL_TEXT)
async def cancel_add_channel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ Bekor qilindi.", reply_markup=admin_menu())


@router.message(StateFilter(AdminAddChannelStates.waiting_username))
async def process_add_channel(message: Message, state: FSMContext):
    raw = (message.text or "").strip()
    if not raw:
        await message.answer("❌ Noto'g'ri qiymat.")
        return

    private_match = PRIVATE_LINK_RE.search(raw)
    if private_match or raw.startswith("+"):
        # Yopiq kanal (invite-link) - chat_id'ni invite-linkdan olib bo'lmaydi,
        # shuning uchun o'sha kanaldan bitta postni forward qilishni so'raymiz.
        invite_link = raw if raw.startswith("http") else f"https://t.me/{raw}"
        await state.update_data(invite_link=invite_link)
        await state.set_state(WAITING_FORWARD_STATE)
        await message.answer(
            "🔒 Bu yopiq kanal linkiga o'xshaydi.\n\n"
            "Iltimos, o'sha kanaldagi istalgan bitta xabarni shu yerga "
            "forward qiling (bot o'sha kanalda admin bo'lishi shart)."
        )
        return

    public_match = PUBLIC_LINK_RE.search(raw)
    username = public_match.group(1) if public_match else raw.lstrip("@")

    if not username:
        await message.answer("❌ Noto'g'ri username yoki link.")
        return

    title = None
    chat_id = None
    try:
        chat = await message.bot.get_chat(f"@{username}")
        title = chat.title
        chat_id = str(chat.id)
    except Exception as e:
        logger.warning(f"Kanal ma'lumotini olishda xatolik @{username}: {e}")

    await channels_repo.add_channel(username=username, title=title, chat_id=chat_id)
    await state.clear()
    await message.answer(f"✅ Kanal qo'shildi: @{username}", reply_markup=admin_menu())


@router.message(StateFilter(WAITING_FORWARD_STATE), F.text == CANCEL_TEXT)
async def cancel_add_channel_forward(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ Bekor qilindi.", reply_markup=admin_menu())


@router.message(StateFilter(WAITING_FORWARD_STATE))
async def process_forwarded_channel_post(message: Message, state: FSMContext):
    # DEBUG: nima kelayotganini logga yozamiz - muammoni aniqlagach o'chirib tashlash mumkin
    logger.info(f"[fwd-debug] forward_from_chat={message.forward_from_chat!r}")
    logger.info(f"[fwd-debug] forward_origin={message.forward_origin!r}")
    if message.forward_origin is not None:
        logger.info(f"[fwd-debug] forward_origin type={type(message.forward_origin)}")

    fwd_chat = getattr(message, "forward_from_chat", None)

    origin = getattr(message, "forward_origin", None)
    if fwd_chat is None and origin is not None:
        # Bot API 7.0+ da forward_origin turlicha bo'lishi mumkin:
        # MessageOriginChannel -> .chat mavjud
        # MessageOriginHiddenUser -> .chat YO'Q (anonim/hidden forward)
        origin_chat = getattr(origin, "chat", None)
        if origin_chat is not None:
            fwd_chat = origin_chat

    if fwd_chat is None or fwd_chat.type != "channel":
        origin_type = getattr(getattr(message, "forward_origin", None), "type", None)
        if origin_type == "hidden_user":
            await message.answer(
                "❌ Bu kanalda \"Sign messages\"/anonim forward yoqilgan bo'lishi mumkin, "
                "shuning uchun bot jo'natuvchi kanalni aniqlay olmayapti.\n\n"
                "Kanal sozlamalaridan \"Hide forwarded from\" ni o'chirib, qayta forward qilib ko'ring."
            )
        else:
            await message.answer(
                "❌ Bu forward qilingan kanal posti emas. "
                "Iltimos, aynan o'sha yopiq kanaldan bitta xabarni forward qiling."
            )
        return

    data = await state.get_data()
    invite_link = data.get("invite_link")

    await channels_repo.add_channel(
        username=fwd_chat.username,
        title=fwd_chat.title,
        chat_id=str(fwd_chat.id),
        invite_link=invite_link,
    )
    await state.clear()
    await message.answer(
        f"✅ Yopiq kanal qo'shildi: {fwd_chat.title}",
        reply_markup=admin_menu(),
    )


@router.message(F.text == "➖ Kanal o'chirish")
async def start_remove_channel(message: Message, state: FSMContext):
    channels = await channels_repo.get_all_channels()
    if not channels:
        await message.answer("Hozircha kanallar mavjud emas.")
        return

    await state.set_state(AdminRemoveChannelStates.waiting_choice)
    await message.answer(
        "🗑 O'chirmoqchi bo'lgan kanalni tanlang:",
        reply_markup=channels_list_keyboard(channels, "remove_ch"),
    )


@router.callback_query(StateFilter(AdminRemoveChannelStates.waiting_choice), F.data.startswith("remove_ch:"))
async def process_remove_channel(callback: CallbackQuery, state: FSMContext):
    channel_id = int(callback.data.split(":")[1])
    success = await channels_repo.remove_channel(channel_id)
    await state.clear()

    if success:
        await callback.message.edit_text("✅ Kanal o'chirildi.")
    else:
        await callback.message.edit_text("❌ Kanal topilmadi.")
    await callback.answer()


@router.message(F.text == "✏ Kanal usernameni o'zgartirish")
async def start_change_channel(message: Message, state: FSMContext):
    channels = await channels_repo.get_all_channels()
    if not channels:
        await message.answer("Hozircha kanallar mavjud emas.")
        return

    await state.set_state(AdminChangeChannelStates.waiting_choice)
    await message.answer(
        "✏ Usernamesini o'zgartirmoqchi bo'lgan kanalni tanlang:",
        reply_markup=channels_list_keyboard(channels, "change_ch"),
    )


@router.callback_query(StateFilter(AdminChangeChannelStates.waiting_choice), F.data.startswith("change_ch:"))
async def choose_channel_to_change(callback: CallbackQuery, state: FSMContext):
    channel_id = int(callback.data.split(":")[1])
    await state.update_data(channel_id=channel_id)
    await state.set_state(AdminChangeChannelStates.waiting_new_username)
    await callback.message.edit_text("✏ Yangi usernameni kiriting (masalan: @newchannel):")
    await callback.answer()


@router.message(StateFilter(AdminChangeChannelStates.waiting_new_username))
async def process_new_channel_username(message: Message, state: FSMContext):
    new_username = message.text.strip().lstrip("@")
    data = await state.get_data()
    channel_id = data["channel_id"]

    success = await channels_repo.update_channel_username(channel_id, new_username)
    await state.clear()

    if success:
        await message.answer(f"✅ Username yangilandi: @{new_username}", reply_markup=admin_menu())
    else:
        await message.answer("❌ Kanal topilmadi.", reply_markup=admin_menu())