"""
Yopiq (invite-link) kanallarga yuborilgan a'zolik so'rovlarini (join
request) saqlaydi. Bot ushbu kanalda admin bo'lishi va yangi a'zolarni
tasdiqlash huquqiga ega bo'lishi shart, aks holda bu update kelmaydi.
"""
from app.database.db import db


async def _ensure_table():
    await db.conn.execute(
        """
        CREATE TABLE IF NOT EXISTS channel_join_requests (
            chat_id TEXT NOT NULL,
            user_id INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            PRIMARY KEY (chat_id, user_id)
        )
        """
    )
    await db.conn.commit()


async def save_join_request(chat_id: str, user_id: int, created_at: str):
    await _ensure_table()
    await db.conn.execute(
        "INSERT OR REPLACE INTO channel_join_requests (chat_id, user_id, created_at) "
        "VALUES (?, ?, ?)",
        (str(chat_id), user_id, created_at),
    )
    await db.conn.commit()


async def has_requested(chat_id: str, user_id: int) -> bool:
    await _ensure_table()
    cursor = await db.conn.execute(
        "SELECT 1 FROM channel_join_requests WHERE chat_id = ? AND user_id = ?",
        (str(chat_id), user_id),
    )
    row = await cursor.fetchone()
    return row is not None