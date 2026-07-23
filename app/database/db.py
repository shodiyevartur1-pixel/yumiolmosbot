"""
Ma'lumotlar bazasi bilan ishlash uchun asosiy modul.
Hozircha SQLite (aiosqlite) ishlatiladi, lekin barcha so'rovlar shu faylda
markazlashtirilgan bo'lgani uchun keyinchalik PostgreSQL'ga o'tish oson
bo'ladi (masalan asyncpg bilan xuddi shu funksiyalarni qayta yozish orqali).
"""
import aiosqlite
from contextlib import asynccontextmanager

from app.config import config

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    first_name TEXT,
    wallet_id TEXT UNIQUE NOT NULL,
    balance INTEGER NOT NULL DEFAULT 0,
    referred_by INTEGER,
    is_banned INTEGER NOT NULL DEFAULT 0,
    registered_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS channels (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id TEXT,
    username TEXT,
    title TEXT,
    invite_link TEXT
);

CREATE TABLE IF NOT EXISTS admins (
    user_id INTEGER PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS withdraws (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    game_id TEXT NOT NULL,
    amount INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    created_at TEXT NOT NULL,
    processed_at TEXT,
    processed_by INTEGER
);

CREATE TABLE IF NOT EXISTS transfers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    from_user INTEGER NOT NULL,
    to_user INTEGER NOT NULL,
    amount INTEGER NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS referrals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    referrer_id INTEGER NOT NULL,
    referred_id INTEGER UNIQUE NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS broadcast_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    admin_id INTEGER,
    total INTEGER,
    sent INTEGER,
    blocked INTEGER,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS diamond_packages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    diamonds INTEGER NOT NULL,
    price INTEGER NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 1,
    sort_order INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS purchases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    package_id INTEGER,
    diamonds INTEGER NOT NULL,
    price INTEGER NOT NULL,
    receipt_file_id TEXT,
    status TEXT NOT NULL DEFAULT 'pending',
    created_at TEXT NOT NULL,
    processed_at TEXT,
    processed_by INTEGER
);

CREATE INDEX IF NOT EXISTS idx_users_wallet ON users(wallet_id);
CREATE INDEX IF NOT EXISTS idx_referrals_referrer ON referrals(referrer_id);
CREATE INDEX IF NOT EXISTS idx_withdraws_status ON withdraws(status);
CREATE INDEX IF NOT EXISTS idx_purchases_status ON purchases(status);
CREATE INDEX IF NOT EXISTS idx_purchases_user ON purchases(user_id);
"""


class Database:
    """
    Ilova davomida bitta ulanish puli saqlanadi (aiosqlite.Connection).
    WAL rejimi yoqilgan - bu bir vaqtning o'zida ko'p o'qish/yozishga
    yordam beradi va 10 000+ foydalanuvchi yukiga chidamli bo'ladi.
    """

    def __init__(self, path: str):
        self.path = path
        self._conn: aiosqlite.Connection | None = None

    async def connect(self):
        self._conn = await aiosqlite.connect(self.path)
        self._conn.row_factory = aiosqlite.Row
        await self._conn.execute("PRAGMA journal_mode=WAL;")
        await self._conn.execute("PRAGMA foreign_keys=ON;")
        await self._conn.executescript(SCHEMA)
        await self._conn.commit()

    async def close(self):
        if self._conn:
            await self._conn.close()

    @property
    def conn(self) -> aiosqlite.Connection:
        if self._conn is None:
            raise RuntimeError("Database ulanmagan. Avval connect() chaqiring.")
        return self._conn

    @asynccontextmanager
    async def transaction(self):
        """
        Atomic tranzaksiyalar uchun context manager.
        Masalan: balansni kamaytirish + transfer yozuvini qo'shish bir vaqtda
        muvaffaqiyatli bo'lishi yoki umuman bo'lmasligi kerak.
        """
        try:
            yield self.conn
            await self.conn.commit()
        except Exception:
            await self.conn.rollback()
            raise


db = Database(config.db_path)