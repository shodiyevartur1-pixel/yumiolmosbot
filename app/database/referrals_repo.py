"""
referrals jadvali - har bir referral faqat bir marta hisoblanishini
kafolatlaydi (referred_id UNIQUE bo'lgani uchun DB darajasida ham himoyalangan).
"""
from datetime import datetime, timezone

from app.database.db import db
from app.database import users_repo
from app.utils.logger import logger


async def already_referred(referred_id: int) -> bool:
    cursor = await db.conn.execute(
        "SELECT 1 FROM referrals WHERE referred_id = ?", (referred_id,)
    )
    row = await cursor.fetchone()
    return row is not None


async def register_referral(referrer_id: int, referred_id: int, bonus: int) -> bool:
    """
    Referral yozuvini qo'shadi va referrerga bonus beradi - hammasi bitta
    atomic tranzaksiyada. Self-referral va duplicate referral bu yerda ham
    qat'iy tekshiriladi (defense in depth).
    Qaytaradi: True - muvaffaqiyatli hisoblandi, False - hisoblanmadi.
    """
    if referrer_id == referred_id:
        return False

    referrer = await users_repo.get_user(referrer_id)
    if referrer is None:
        return False

    if await already_referred(referred_id):
        return False

    now = datetime.now(timezone.utc).isoformat()
    try:
        async with db.transaction() as conn:
            await conn.execute(
                """
                INSERT INTO referrals (referrer_id, referred_id, created_at)
                VALUES (?, ?, ?)
                """,
                (referrer_id, referred_id, now),
            )
            await users_repo.add_balance(referrer_id, bonus, conn=conn)
    except Exception as e:
        logger.warning(f"Referral qo'shishda xatolik (ehtimol duplicate): {e}")
        return False

    logger.info(f"Referral hisoblandi: referrer={referrer_id} referred={referred_id} bonus={bonus}")
    return True


async def count_referrals(referrer_id: int) -> int:
    cursor = await db.conn.execute(
        "SELECT COUNT(*) as c FROM referrals WHERE referrer_id = ?", (referrer_id,)
    )
    row = await cursor.fetchone()
    return row["c"]


async def count_today_referrals(referrer_id: int) -> int:
    today = datetime.now(timezone.utc).date().isoformat()
    cursor = await db.conn.execute(
        "SELECT COUNT(*) as c FROM referrals WHERE referrer_id = ? AND created_at LIKE ?",
        (referrer_id, f"{today}%"),
    )
    row = await cursor.fetchone()
    return row["c"]


async def get_top_referrers(limit: int = 100):
    cursor = await db.conn.execute(
        """
        SELECT u.user_id, u.username, u.first_name, COUNT(r.id) as ref_count
        FROM referrals r
        JOIN users u ON u.user_id = r.referrer_id
        GROUP BY r.referrer_id
        ORDER BY ref_count DESC
        LIMIT ?
        """,
        (limit,),
    )
    return await cursor.fetchall()
