"""
Majburiy obuna kanallari bilan ishlash.
Kanallar soni cheklanmagan (unlimited).

Ikki xil kanal qo'llab-quvvatlanadi:
- Ochiq kanal (username orqali): chat_id + username saqlanadi.
- Yopiq kanal (invite-link, "a'zolikni tasdiqlash" yoqilgan): chat_id
  (kanaldan forward qilingan xabar orqali aniqlanadi) + invite_link
  saqlanadi, username odatda bo'lmaydi (None).
"""
from app.database.db import db


async def _ensure_columns():
    """
    Eski bazalarda `channels.username` ustuni NOT NULL bo'lib qolgan bo'lishi
    mumkin (dastlabki sxema shunday yaratilgan edi). Bu yopiq (invite-link)
    kanallar uchun mos emas, chunki ularda username umuman bo'lmaydi.

    SQLite'da ustundan NOT NULL'ni to'g'ridan-to'g'ri olib tashlab bo'lmaydi,
    shuning uchun kerak bo'lsa jadval qayta quriladi (mavjud ma'lumotlar
    saqlanib qoladi).
    """
    cursor = await db.conn.execute("PRAGMA table_info(channels)")
    columns = await cursor.fetchall()
    col_map = {row["name"]: row for row in columns}

    username_not_null = "username" in col_map and col_map["username"]["notnull"] == 1

    if username_not_null:
        has_invite_link = "invite_link" in col_map
        await db.conn.execute(
            """
            CREATE TABLE channels_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id TEXT,
                username TEXT,
                title TEXT,
                invite_link TEXT
            )
            """
        )
        if has_invite_link:
            await db.conn.execute(
                """
                INSERT INTO channels_new (id, chat_id, username, title, invite_link)
                SELECT id, chat_id, username, title, invite_link FROM channels
                """
            )
        else:
            await db.conn.execute(
                """
                INSERT INTO channels_new (id, chat_id, username, title)
                SELECT id, chat_id, username, title FROM channels
                """
            )
        await db.conn.execute("DROP TABLE channels")
        await db.conn.execute("ALTER TABLE channels_new RENAME TO channels")
        await db.conn.commit()
    elif "invite_link" not in col_map:
        await db.conn.execute("ALTER TABLE channels ADD COLUMN invite_link TEXT")
        await db.conn.commit()


async def add_channel(
    username: str | None = None,
    title: str | None = None,
    chat_id: str | None = None,
    invite_link: str | None = None,
):
    await _ensure_columns()
    await db.conn.execute(
        "INSERT INTO channels (chat_id, username, title, invite_link) VALUES (?, ?, ?, ?)",
        (chat_id, username, title, invite_link),
    )
    await db.conn.commit()


async def remove_channel(channel_id: int) -> bool:
    cursor = await db.conn.execute(
        "DELETE FROM channels WHERE id = ?", (channel_id,)
    )
    await db.conn.commit()
    return cursor.rowcount > 0


async def remove_channel_by_username(username: str) -> bool:
    username = username.lstrip("@")
    cursor = await db.conn.execute(
        "DELETE FROM channels WHERE username = ?", (username,)
    )
    await db.conn.commit()
    return cursor.rowcount > 0


async def update_channel_username(channel_id: int, new_username: str) -> bool:
    new_username = new_username.lstrip("@")
    cursor = await db.conn.execute(
        "UPDATE channels SET username = ? WHERE id = ?", (new_username, channel_id)
    )
    await db.conn.commit()
    return cursor.rowcount > 0


async def get_all_channels():
    await _ensure_columns()
    cursor = await db.conn.execute("SELECT * FROM channels ORDER BY id")
    return await cursor.fetchall()