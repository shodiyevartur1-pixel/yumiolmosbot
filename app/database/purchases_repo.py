"""
purchases jadvali - foydalanuvchi karta orqali Almaz sotib olganda shu
yerga "pending" holatda yoziladi. Admin tasdiqlagandan so'ng Almaz
avtomatik foydalanuvchi balansiga qo'shiladi.
"""
from datetime import datetime, timezone

from app.database.db import db
from app.database import users_repo
from app.utils.logger import logger


async def create_purchase(
    user_id: int,
    package_id: int | None,
    diamonds: int,
    price: int,
    receipt_file_id: str,
) -> int:
    now = datetime.now(timezone.utc).isoformat()
    cursor = await db.conn.execute(
        """
        INSERT INTO purchases (user_id, package_id, diamonds, price,
                                receipt_file_id, status, created_at)
        VALUES (?, ?, ?, ?, ?, 'pending', ?)
        """,
        (user_id, package_id, diamonds, price, receipt_file_id, now),
    )
    await db.conn.commit()
    logger.info(
        f"Almaz xarid so'rovi yaratildi: user={user_id} diamonds={diamonds} price={price}"
    )
    return cursor.lastrowid


async def get_purchase(purchase_id: int):
    cursor = await db.conn.execute(
        "SELECT * FROM purchases WHERE id = ?", (purchase_id,)
    )
    return await cursor.fetchone()


async def approve_purchase(purchase_id: int, admin_id: int) -> tuple[bool, str]:
    """
    Tasdiqlash: paketdagi Almaz miqdorini foydalanuvchi balansiga qo'shadi
    va so'rov holatini 'approved' ga o'zgartiradi. Hammasi atomic.
    """
    purchase = await get_purchase(purchase_id)
    if purchase is None:
        return False, "So'rov topilmadi."
    if purchase["status"] != "pending":
        return False, "Bu so'rov allaqachon ko'rib chiqilgan."

    now = datetime.now(timezone.utc).isoformat()
    async with db.transaction() as conn:
        await users_repo.add_balance(purchase["user_id"], purchase["diamonds"], conn=conn)
        await conn.execute(
            """
            UPDATE purchases SET status = 'approved', processed_at = ?, processed_by = ?
            WHERE id = ?
            """,
            (now, admin_id, purchase_id),
        )

    logger.info(f"Almaz xaridi tasdiqlandi: id={purchase_id} admin={admin_id}")
    return True, "Tasdiqlandi."


async def reject_purchase(purchase_id: int, admin_id: int) -> tuple[bool, str]:
    purchase = await get_purchase(purchase_id)
    if purchase is None:
        return False, "So'rov topilmadi."
    if purchase["status"] != "pending":
        return False, "Bu so'rov allaqachon ko'rib chiqilgan."

    now = datetime.now(timezone.utc).isoformat()
    await db.conn.execute(
        """
        UPDATE purchases SET status = 'rejected', processed_at = ?, processed_by = ?
        WHERE id = ?
        """,
        (now, admin_id, purchase_id),
    )
    await db.conn.commit()
    logger.info(f"Almaz xaridi rad etildi: id={purchase_id} admin={admin_id}")
    return True, "Rad etildi."


async def get_user_purchase_history(user_id: int, limit: int = 20):
    cursor = await db.conn.execute(
        "SELECT * FROM purchases WHERE user_id = ? ORDER BY id DESC LIMIT ?",
        (user_id, limit),
    )
    return await cursor.fetchall()