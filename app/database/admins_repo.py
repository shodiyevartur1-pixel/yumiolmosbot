"""
admins jadvali - .env ichidagi ADMIN_IDS bazaviy adminlar hisoblanadi,
lekin ular ham shu jadvalga sinxronlanadi, shunda admin qo'shish/o'chirish
runtime'da (bot qayta ishga tushmasdan) ham ishlashi mumkin.
"""
from app.database.db import db
from app.config import config


async def sync_env_admins():
    for admin_id in config.admin_ids:
        await db.conn.execute(
            "INSERT OR IGNORE INTO admins (user_id) VALUES (?)", (admin_id,)
        )
    await db.conn.commit()


async def is_admin(user_id: int) -> bool:
    if user_id in config.admin_ids:
        return True
    cursor = await db.conn.execute(
        "SELECT 1 FROM admins WHERE user_id = ?", (user_id,)
    )
    row = await cursor.fetchone()
    return row is not None


async def add_admin(user_id: int):
    await db.conn.execute(
        "INSERT OR IGNORE INTO admins (user_id) VALUES (?)", (user_id,)
    )
    await db.conn.commit()


async def remove_admin(user_id: int):
    await db.conn.execute("DELETE FROM admins WHERE user_id = ?", (user_id,))
    await db.conn.commit()


async def get_all_admins() -> list[int]:
    cursor = await db.conn.execute("SELECT user_id FROM admins")
    rows = await cursor.fetchall()
    ids = {r["user_id"] for r in rows}
    ids.update(config.admin_ids)
    return list(ids)
