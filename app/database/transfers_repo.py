"""
transfers jadvali - foydalanuvchidan foydalanuvchiga Yumi Almaz o'tkazmalari.
"""
from datetime import datetime, timezone
from enum import Enum

from app.database.db import db
from app.database import users_repo
from app.utils.logger import logger


class TransferResult(str, Enum):
    OK = "ok"
    NOT_FOUND = "not_found"
    SELF = "self"
    INSUFFICIENT = "insufficient"
    BANNED = "banned"


async def transfer(from_user_id: int, wallet_id: str, amount: int) -> tuple[TransferResult, dict | None]:
    """
    Atomic transfer: yuboruvchidan yechish va qabul qiluvchiga qo'shish
    bitta tranzaksiyada bajariladi, shu bilan birga negative balans
    bo'lishining oldi olinadi (subtract_balance_atomic sharti orqali).
    """
    receiver = await users_repo.get_user_by_wallet(wallet_id)
    if receiver is None:
        return TransferResult.NOT_FOUND, None

    if receiver["user_id"] == from_user_id:
        return TransferResult.SELF, None

    if receiver["is_banned"]:
        return TransferResult.BANNED, None

    now = datetime.now(timezone.utc).isoformat()

    async with db.transaction() as conn:
        success = await users_repo.subtract_balance_atomic(from_user_id, amount, conn)
        if not success:
            # rollback avtomatik bo'lmaydi chunki hali xatolik ko'tarilmadi,
            # shuning uchun aniq qaytaramiz
            return TransferResult.INSUFFICIENT, None

        await users_repo.add_balance(receiver["user_id"], amount, conn=conn)
        await conn.execute(
            """
            INSERT INTO transfers (from_user, to_user, amount, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (from_user_id, receiver["user_id"], amount, now),
        )

    logger.info(f"Transfer: {from_user_id} -> {receiver['user_id']} ({wallet_id}) amount={amount}")
    return TransferResult.OK, dict(receiver)


async def get_user_transfer_history(user_id: int, limit: int = 20):
    cursor = await db.conn.execute(
        """
        SELECT t.*, 
               us.wallet_id as sender_wallet, us.username as sender_username,
               ur.wallet_id as receiver_wallet, ur.username as receiver_username
        FROM transfers t
        JOIN users us ON us.user_id = t.from_user
        JOIN users ur ON ur.user_id = t.to_user
        WHERE t.from_user = ? OR t.to_user = ?
        ORDER BY t.id DESC
        LIMIT ?
        """,
        (user_id, user_id, limit),
    )
    return await cursor.fetchall()


async def get_all_transfers(limit: int = 100):
    cursor = await db.conn.execute(
        """
        SELECT t.*, 
               us.wallet_id as sender_wallet, us.username as sender_username,
               ur.wallet_id as receiver_wallet, ur.username as receiver_username
        FROM transfers t
        JOIN users us ON us.user_id = t.from_user
        JOIN users ur ON ur.user_id = t.to_user
        ORDER BY t.id DESC
        LIMIT ?
        """,
        (limit,),
    )
    return await cursor.fetchall()
