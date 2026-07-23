"""
settings jadvali - admin tomonidan o'zgartiriladigan parametrlar
(referral bonusi, minimal yechish miqdori va h.k.) shu yerda saqlanadi.
"""
from app.database.db import db
from app.config import config

REFERRAL_BONUS_KEY = "referral_bonus"
MIN_WITHDRAW_KEY = "min_withdraw"
CARD_OWNER_KEY = "card_owner"
CARD_NUMBER_KEY = "card_number"
PAYMENT_NOTE_KEY = "payment_note"
PAYMENT_ENABLED_KEY = "payment_enabled"


async def ensure_defaults():
    await _set_if_absent(REFERRAL_BONUS_KEY, str(config.default_referral_bonus))
    await _set_if_absent(MIN_WITHDRAW_KEY, str(config.default_min_withdraw))
    await _set_if_absent(CARD_OWNER_KEY, config.default_card_owner)
    await _set_if_absent(CARD_NUMBER_KEY, config.default_card_number)
    await _set_if_absent(PAYMENT_NOTE_KEY, config.default_payment_note)
    await _set_if_absent(PAYMENT_ENABLED_KEY, "1" if config.default_payment_enabled else "0")


async def _set_if_absent(key: str, value: str):
    await db.conn.execute(
        "INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (key, value)
    )
    await db.conn.commit()


async def get_setting(key: str, default: str = "") -> str:
    cursor = await db.conn.execute(
        "SELECT value FROM settings WHERE key = ?", (key,)
    )
    row = await cursor.fetchone()
    return row["value"] if row else default


async def set_setting(key: str, value: str):
    await db.conn.execute(
        """
        INSERT INTO settings (key, value) VALUES (?, ?)
        ON CONFLICT(key) DO UPDATE SET value = excluded.value
        """,
        (key, value),
    )
    await db.conn.commit()


async def get_referral_bonus() -> int:
    value = await get_setting(REFERRAL_BONUS_KEY, str(config.default_referral_bonus))
    return int(value)


async def set_referral_bonus(amount: int):
    await set_setting(REFERRAL_BONUS_KEY, str(amount))


async def get_min_withdraw() -> int:
    value = await get_setting(MIN_WITHDRAW_KEY, str(config.default_min_withdraw))
    return int(value)


async def set_min_withdraw(amount: int):
    await set_setting(MIN_WITHDRAW_KEY, str(amount))


async def get_card_owner() -> str:
    return await get_setting(CARD_OWNER_KEY, config.default_card_owner)


async def set_card_owner(value: str):
    await set_setting(CARD_OWNER_KEY, value)


async def get_card_number() -> str:
    return await get_setting(CARD_NUMBER_KEY, config.default_card_number)


async def set_card_number(value: str):
    await set_setting(CARD_NUMBER_KEY, value)


async def get_payment_note() -> str:
    return await get_setting(PAYMENT_NOTE_KEY, config.default_payment_note)


async def set_payment_note(value: str):
    await set_setting(PAYMENT_NOTE_KEY, value)


async def get_payment_enabled() -> bool:
    value = await get_setting(
        PAYMENT_ENABLED_KEY, "1" if config.default_payment_enabled else "0"
    )
    return value == "1"


async def set_payment_enabled(enabled: bool):
    await set_setting(PAYMENT_ENABLED_KEY, "1" if enabled else "0")