"""
Konfiguratsiya moduli.
Barcha muhim sozlamalar .env fayldan o'qiladi.
"""
import os
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()


def _parse_admin_ids(raw: str) -> list[int]:
    if not raw:
        return []
    result = []
    for part in raw.split(","):
        part = part.strip()
        if part.isdigit():
            result.append(int(part))
    return result


@dataclass
class Config:
    bot_token: str = os.getenv("BOT_TOKEN", "")
    admin_ids: list[int] = field(default_factory=lambda: _parse_admin_ids(os.getenv("ADMIN_IDS", "")))
    db_path: str = os.getenv("DB_PATH", "yumi_almaz.db")
    log_path: str = os.getenv("LOG_PATH", "logs/bot.log")

    # Standart qiymatlar (keyinchalik settings jadvalida saqlanadi va admin
    # tomonidan o'zgartiriladi, bu yerda faqat "birinchi ishga tushirish"
    # uchun standart qiymat sifatida ishlatiladi)
    default_referral_bonus: int = int(os.getenv("DEFAULT_REFERRAL_BONUS", "30"))
    default_min_withdraw: int = int(os.getenv("DEFAULT_MIN_WITHDRAW", "300"))

    # To'lov tizimi uchun standart qiymatlar (keyinchalik "settings" jadvalida
    # saqlanadi va admin panel orqali istalgan vaqtda o'zgartiriladi)
    default_card_owner: str = os.getenv("DEFAULT_CARD_OWNER", "Admin")
    default_card_number: str = os.getenv("DEFAULT_CARD_NUMBER", "9860 6067 5238 6163")
    default_payment_note: str = os.getenv(
        "DEFAULT_PAYMENT_NOTE",
        "To'lovni amalga oshirgandan so'ng \"✅ To'lov qildim\" tugmasini bosing "
        "va chek (screenshot) ni yuboring.",
    )
    default_payment_enabled: bool = os.getenv("DEFAULT_PAYMENT_ENABLED", "1") == "1"

    # Flood / rate limit sozlamalari
    rate_limit_seconds: float = float(os.getenv("RATE_LIMIT_SECONDS", "0.7"))


config = Config()

if not config.bot_token:
    raise RuntimeError(
        "BOT_TOKEN topilmadi. Iltimos .env faylga BOT_TOKEN=... qatorini qo'shing."
    )