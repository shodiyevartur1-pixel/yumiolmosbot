"""
diamond_packages jadvali - "Almaz sotib olish" bo'limida foydalanuvchiga
ko'rsatiladigan paketlar (miqdor + narx). Admin panel orqali qo'shiladi
va o'chiriladi.
"""
from app.database.db import db


async def add_package(diamonds: int, price: int) -> int:
    cursor = await db.conn.execute(
        """
        INSERT INTO diamond_packages (diamonds, price, is_active, sort_order)
        VALUES (?, ?, 1, ?)
        """,
        (diamonds, price, price),
    )
    await db.conn.commit()
    return cursor.lastrowid


async def get_package(package_id: int):
    cursor = await db.conn.execute(
        "SELECT * FROM diamond_packages WHERE id = ?", (package_id,)
    )
    return await cursor.fetchone()


async def get_all_packages(active_only: bool = False):
    if active_only:
        cursor = await db.conn.execute(
            "SELECT * FROM diamond_packages WHERE is_active = 1 "
            "ORDER BY sort_order ASC, price ASC"
        )
    else:
        cursor = await db.conn.execute(
            "SELECT * FROM diamond_packages ORDER BY sort_order ASC, price ASC"
        )
    return await cursor.fetchall()


async def remove_package(package_id: int) -> bool:
    cursor = await db.conn.execute(
        "DELETE FROM diamond_packages WHERE id = ?", (package_id,)
    )
    await db.conn.commit()
    return cursor.rowcount > 0


async def set_active(package_id: int, active: bool) -> bool:
    cursor = await db.conn.execute(
        "UPDATE diamond_packages SET is_active = ? WHERE id = ?",
        (1 if active else 0, package_id),
    )
    await db.conn.commit()
    return cursor.rowcount > 0