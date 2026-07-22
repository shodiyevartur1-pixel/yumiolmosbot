"""
Majburiy obuna: foydalanuvchi barcha kerakli kanallarga a'zo bo'lganmi
tekshiradi.

- Ochiq kanallar (username orqali qo'shilgan): get_chat_member orqali
  to'g'ridan-to'g'ri tekshiriladi.
- Yopiq kanallar (invite-link orqali qo'shilgan, "a'zolikni tasdiqlash"
  yoqilgan): foydalanuvchi kanalga zayavka (join request) yuborganmi
  tekshiriladi - agar yuborgan bo'lsa, obuna bo'lgan deb hisoblanadi
  (admin hali tasdiqlamagan bo'lsa ham).
"""
from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError

from app.database import channels_repo, join_requests_repo
from app.utils.logger import logger

SUBSCRIBED_STATUSES = {"member", "administrator", "creator"}


async def get_not_subscribed_channels(bot: Bot, user_id: int) -> list:
    channels = await channels_repo.get_all_channels()
    logger.info(f"[sub-debug] user={user_id} jami kanallar={len(channels)}")
    not_subscribed = []

    for channel in channels:
        invite_link = channel["invite_link"] if "invite_link" in channel.keys() else None
        logger.info(
            f"[sub-debug] tekshirilyapti: id={channel['id']} title={channel['title']!r} "
            f"chat_id={channel['chat_id']!r} username={channel['username']!r} "
            f"invite_link={invite_link!r}"
        )

        if invite_link:
            requested = await join_requests_repo.has_requested(channel["chat_id"], user_id)
            logger.info(f"[sub-debug] yopiq kanal, join_request bazada bormi: {requested}")
            if requested:
                continue

            # Zaxira tekshiruv: join_requests jadvalida yozuv topilmadi
            # (masalan chat_join_request update'i o'sha vaqtda qo'lga
            # tushmagan bo'lishi mumkin), lekin foydalanuvchi haqiqatda
            # kanalga a'zo bo'lgan bo'lishi mumkin - shuni ham tekshiramiz.
            if channel["chat_id"]:
                try:
                    member = await bot.get_chat_member(channel["chat_id"], user_id)
                    logger.info(f"[sub-debug] get_chat_member natijasi: {member.status}")
                    if member.status in SUBSCRIBED_STATUSES:
                        continue
                except (TelegramBadRequest, TelegramForbiddenError) as e:
                    logger.info(f"[sub-debug] get_chat_member xato (Bad/Forbidden): {e}")
                except Exception as e:
                    logger.info(f"[sub-debug] get_chat_member kutilmagan xato: {e}")

            not_subscribed.append(channel)
            continue

        target = channel["chat_id"] or f"@{channel['username']}"
        try:
            member = await bot.get_chat_member(target, user_id)
            logger.info(f"[sub-debug] ochiq kanal get_chat_member natijasi: {member.status}")
            if member.status not in SUBSCRIBED_STATUSES:
                not_subscribed.append(channel)
        except (TelegramBadRequest, TelegramForbiddenError) as e:
            logger.info(f"[sub-debug] ochiq kanal xato (Bad/Forbidden): {e}")
            not_subscribed.append(channel)
        except Exception as e:
            logger.info(f"[sub-debug] ochiq kanal kutilmagan xato: {e}")
            not_subscribed.append(channel)

    logger.info(f"[sub-debug] natija: obuna bo'lmagan kanallar soni={len(not_subscribed)}")
    return not_subscribed
