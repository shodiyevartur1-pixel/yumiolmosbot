"""
Wallet ID generatsiya qilish uchun util.
Format: 5 ta belgi, katta harflar (A-Z) va raqamlar (0-9) aralash.
Masalan: MK7T3, HJ8KL, TR5P9, AB2XM
"""
import random
import string

ALPHABET = string.ascii_uppercase + string.digits


def generate_wallet_id(length: int = 5) -> str:
    return "".join(random.choices(ALPHABET, k=length))
