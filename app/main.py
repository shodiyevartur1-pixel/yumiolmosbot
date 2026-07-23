"""
Yumi Almaz Telegram Bot - asosiy kirish nuqtasi.

Ishga tushirish:
    python -m app.main
"""
import asyncio

from app.loader import bot, dp
from app.database.db import db
from app.database import admins_repo, settings_repo
from app.middlewares.throttling import ThrottlingMiddleware
from app.middlewares.ban_check import BanCheckMiddleware
from app.utils.logger import logger

# --- Handlers (routerlar) ---
from app.handlers import start as start_handler
from app.handlers import profile as profile_handler
from app.handlers import purchase as purchase_handler
from app.handlers import referral as referral_handler
from app.handlers import balance as balance_handler
from app.handlers import transfer as transfer_handler
from app.handlers import withdraw as withdraw_handler
from app.handlers import history as history_handler
from app.handlers import help as help_handler
from app.handlers import admin_stats as admin_stats_handler
from app.handlers import admin_channels as admin_channels_handler
from app.handlers import admin_settings as admin_settings_handler
from app.handlers import admin_balance as admin_balance_handler
from app.handlers import admin_users as admin_users_handler
from app.handlers import admin_broadcast as admin_broadcast_handler
from app.handlers import admin_restart as admin_restart_handler
from app.handlers import channel_join_requests as channel_join_requests_handler


def register_middlewares():
    dp.message.middleware(BanCheckMiddleware())
    dp.callback_query.middleware(BanCheckMiddleware())
    dp.message.middleware(ThrottlingMiddleware())


def register_routers():
    # Tartib muhim: aniqroq (masalan admin state'lari) routerlar birinchi
    # bo'lib tekshiriladi, umumiy routerlar keyin.
    dp.include_router(start_handler.router)
    dp.include_router(channel_join_requests_handler.router)
    dp.include_router(admin_broadcast_handler.router)
    dp.include_router(admin_channels_handler.router)
    dp.include_router(admin_settings_handler.router)
    dp.include_router(admin_balance_handler.router)
    dp.include_router(admin_users_handler.router)
    dp.include_router(admin_stats_handler.router)
    dp.include_router(admin_restart_handler.router)
    dp.include_router(profile_handler.router)
    dp.include_router(purchase_handler.router)
    dp.include_router(referral_handler.router)
    dp.include_router(balance_handler.router)
    dp.include_router(transfer_handler.router)
    dp.include_router(withdraw_handler.router)
    dp.include_router(history_handler.router)
    dp.include_router(help_handler.router)


async def on_startup():
    await db.connect()
    await admins_repo.sync_env_admins()
    await settings_repo.ensure_defaults()
    logger.info("Bot ishga tushdi.")


async def on_shutdown():
    await db.close()
    logger.info("Bot to'xtatildi.")


async def main():
    register_middlewares()
    register_routers()

    await on_startup()
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    finally:
        await on_shutdown()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot qo'lda to'xtatildi.")