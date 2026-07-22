"""
withdraws jadvali - Yumi Almazni yechib olish so'rovlari.
Balans faqat admin tasdiqlaganidan keyin yechiladi.
"""
from datetime import datetime, timezone

from app.database.db import db
from app.database import users_repo
from app.utils.logger import logger


async def create_withdraw_request(user_id: int, game_id: str, amount: int) -> int:
    now = datetime.now(timezone.utc).isoformat()
    cursor = await db.conn.execute(
        """
        INSERT INTO withdraws (user_id, game_id, amount, status, created_at)
        VALUES (?, ?, ?, 'pending', ?)
        """,
        (user_id, game_id, amount, now),
    )
    await db.conn.commit()
    logger.info(f"Yechish so'rovi yaratildi: user={user_id} amount={amount} game_id={game_id}")
    return cursor.lastrowid


async def get_withdraw(withdraw_id: int):
    cursor = await db.conn.execute(
        "SELECT * FROM withdraws WHERE id = ?", (withdraw_id,)
    )
    return await cursor.fetchone()


async def approve_withdraw(withdraw_id: int, admin_id: int) -> tuple[bool, str]:
    """
    Tasdiqlash: balansni tekshiradi va yechadi (agar hali yetarli bo'lsa),
    so'rov holatini 'approved' ga o'zgartiradi. Hammasi atomic.
    """
    withdraw = await get_withdraw(withdraw_id)
    if withdraw is None:
        return False, "So'rov topilmadi."
    if withdraw["status"] != "pending":
        return False, "Bu so'rov allaqachon ko'rib chiqilgan."

    now = datetime.now(timezone.utc).isoformat()
    async with db.transaction() as conn:
        success = await users_repo.subtract_balance_atomic(
            withdraw["user_id"], withdraw["amount"], conn
        )
        if not success:
            return False, "Foydalanuvchi balansi yetarli emas."

        await conn.execute(
            """
            UPDATE withdraws SET status = 'approved', processed_at = ?, processed_by = ?
            WHERE id = ?
            """,
            (now, admin_id, withdraw_id),
        )

    logger.info(f"Yechish so'rovi tasdiqlandi: id={withdraw_id} admin={admin_id}")
    return True, "Tasdiqlandi."


async def reject_withdraw(withdraw_id: int, admin_id: int) -> tuple[bool, str]:
    withdraw = await get_withdraw(withdraw_id)
    if withdraw is None:
        return False, "So'rov topilmadi."
    if withdraw["status"] != "pending":
        return False, "Bu so'rov allaqachon ko'rib chiqilgan."

    now = datetime.now(timezone.utc).isoformat()
    await db.conn.execute(
        """
        UPDATE withdraws SET status = 'rejected', processed_at = ?, processed_by = ?
        WHERE id = ?
        """,
        (now, admin_id, withdraw_id),
    )
    await db.conn.commit()
    logger.info(f"Yechish so'rovi bekor qilindi: id={withdraw_id} admin={admin_id}")
    return True, "Bekor qilindi."


async def get_user_withdraw_history(user_id: int, limit: int = 20):
    cursor = await db.conn.execute(
        """
        SELECT * FROM withdraws WHERE user_id = ? ORDER BY id DESC LIMIT ?
        """,
        (user_id, limit),
    )
    return await cursor.fetchall()


async def get_all_withdraws(limit: int = 100):
    cursor = await db.conn.execute(
        """
        SELECT w.*, u.username, u.wallet_id FROM withdraws w
        JOIN users u ON u.user_id = w.user_id
        ORDER BY w.id DESC LIMIT ?
        """,
        (limit,),
    )
    return await cursor.fetchall()
