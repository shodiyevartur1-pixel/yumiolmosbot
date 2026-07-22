"""
users jadvali bilan bog'liq barcha so'rovlar shu yerda.
"""
from datetime import datetime, timezone

from app.database.db import db
from app.utils.wallet_id import generate_wallet_id
from app.utils.logger import logger


async def _wallet_id_exists(wallet_id: str) -> bool:
    cursor = await db.conn.execute(
        "SELECT 1 FROM users WHERE wallet_id = ?", (wallet_id,)
    )
    row = await cursor.fetchone()
    return row is not None


async def _generate_unique_wallet_id() -> str:
    while True:
        wallet_id = generate_wallet_id()
        if not await _wallet_id_exists(wallet_id):
            return wallet_id


async def get_user(user_id: int):
    cursor = await db.conn.execute(
        "SELECT * FROM users WHERE user_id = ?", (user_id,)
    )
    return await cursor.fetchone()


async def get_user_by_wallet(wallet_id: str):
    cursor = await db.conn.execute(
        "SELECT * FROM users WHERE wallet_id = ?", (wallet_id.upper(),)
    )
    return await cursor.fetchone()


async def user_exists(user_id: int) -> bool:
    return await get_user(user_id) is not None


async def create_user(
    user_id: int,
    username: str | None,
    first_name: str | None,
    referred_by: int | None = None,
) -> str:
    """
    Yangi user yaratadi va noyob Wallet ID qaytaradi.
    referred_by faqat haqiqiy (mavjud, o'zi bo'lmagan) referrer bo'lsagina
    saqlanadi - bu tekshiruv handler darajasida ham bajariladi, lekin
    xavfsizlik uchun bu yerda ham qat'iy saqlanadi.
    """
    wallet_id = await _generate_unique_wallet_id()
    now = datetime.now(timezone.utc).isoformat()

    async with db.transaction() as conn:
        await conn.execute(
            """
            INSERT INTO users (user_id, username, first_name, wallet_id,
                                balance, referred_by, is_banned, registered_at)
            VALUES (?, ?, ?, ?, 0, ?, 0, ?)
            """,
            (user_id, username, first_name, wallet_id, referred_by, now),
        )

    logger.info(f"Yangi user ro'yxatdan o'tdi: {user_id} wallet={wallet_id}")
    return wallet_id


async def update_username(user_id: int, username: str | None, first_name: str | None):
    await db.conn.execute(
        "UPDATE users SET username = ?, first_name = ? WHERE user_id = ?",
        (username, first_name, user_id),
    )
    await db.conn.commit()


async def is_banned(user_id: int) -> bool:
    user = await get_user(user_id)
    return bool(user["is_banned"]) if user else False


async def set_ban(user_id: int, banned: bool):
    await db.conn.execute(
        "UPDATE users SET is_banned = ? WHERE user_id = ?",
        (1 if banned else 0, user_id),
    )
    await db.conn.commit()


async def get_balance(user_id: int) -> int:
    user = await get_user(user_id)
    return user["balance"] if user else 0


async def add_balance(user_id: int, amount: int, conn=None):
    """
    Balansga qo'shish. conn berilsa mavjud tranzaksiya ichida ishlaydi,
    aks holda alohida commit qiladi.
    """
    target_conn = conn or db.conn
    await target_conn.execute(
        "UPDATE users SET balance = balance + ? WHERE user_id = ?",
        (amount, user_id),
    )
    if conn is None:
        await target_conn.commit()


async def subtract_balance_atomic(user_id: int, amount: int, conn) -> bool:
    """
    Balansni faqat yetarli mablag' bo'lsa kamaytiradi (negative balans
    bo'lishining oldini olish uchun WHERE balance >= amount sharti bilan).
    Tranzaksiya ichida chaqirilishi kerak (conn majburiy).
    Qaytaradi: True - muvaffaqiyatli, False - balans yetarli emas.
    """
    cursor = await conn.execute(
        "UPDATE users SET balance = balance - ? WHERE user_id = ? AND balance >= ?",
        (amount, user_id, amount),
    )
    return cursor.rowcount > 0


async def count_users() -> int:
    cursor = await db.conn.execute("SELECT COUNT(*) as c FROM users")
    row = await cursor.fetchone()
    return row["c"]


async def count_today_users() -> int:
    today = datetime.now(timezone.utc).date().isoformat()
    cursor = await db.conn.execute(
        "SELECT COUNT(*) as c FROM users WHERE registered_at LIKE ?",
        (f"{today}%",),
    )
    row = await cursor.fetchone()
    return row["c"]


async def get_all_user_ids() -> list[int]:
    cursor = await db.conn.execute("SELECT user_id FROM users WHERE is_banned = 0")
    rows = await cursor.fetchall()
    return [r["user_id"] for r in rows]


async def search_user(query: str):
    """
    Username, ism yoki Telegram ID / Wallet ID bo'yicha qidirish.
    """
    query = query.strip().lstrip("@")
    if query.isdigit():
        cursor = await db.conn.execute(
            "SELECT * FROM users WHERE user_id = ?", (int(query),)
        )
    else:
        cursor = await db.conn.execute(
            """
            SELECT * FROM users
            WHERE username LIKE ? OR wallet_id = ? OR first_name LIKE ?
            LIMIT 20
            """,
            (f"%{query}%", query.upper(), f"%{query}%"),
        )
        rows = await cursor.fetchall()
        return rows
    return await cursor.fetchone()
