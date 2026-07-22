# Yumi Almaz Telegram Bot

Referral + Diamond Wallet tizimiga ega professional Telegram bot.
Python 3.12+, aiogram 3.x, SQLite (aiosqlite), to'liq async arxitektura.

## Imkoniyatlar

- **Majburiy kanal a'zoligi** — cheksiz sonli kanal, admin panel orqali boshqariladi
- **Ro'yxatdan o'tish** — har bir foydalanuvchi uchun noyob, doimiy Wallet ID (masalan `MK7T3`)
- **Referral tizimi** — har bir referral uchun 💎 bonus (standart 30, admin o'zgartira oladi), self/duplicate referral himoyalangan
- **Top 100 referral** reytingi
- **Yumi Almaz hamyoni** — balans, Wallet ID orqali boshqa foydalanuvchiga o'tkazma
- **Yechib olish** — Game ID orqali so'rov, admin tasdiqlaydi/bekor qiladi
- **To'liq admin panel** — statistika, reklama (broadcast), kanal boshqaruvi, balans qo'shish/ayirish, user qidirish, ban/unban, tarixlar, sozlamalar, restart
- **Xavfsizlik** — atomic tranzaksiyalar, negative balans himoyasi, parametrli SQL so'rovlar, flood/rate-limit himoyasi, to'liq logging

## O'rnatish

```bash
git clone <repo>
cd YumiAlmazBot
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

`.env` faylini oching va quyidagilarni to'ldiring:

```
BOT_TOKEN=sizning_bot_tokeningiz
ADMIN_IDS=123456789
```

## Ishga tushirish

```bash
python -m app.main
```

## Loyiha strukturasi

```
YumiAlmazBot/
├── app/
│   ├── handlers/        # /start, profil, referral, transfer, withdraw, admin va h.k.
│   ├── middlewares/      # ban tekshiruvi, flood himoyasi
│   ├── filters/          # IsAdmin filtri
│   ├── keyboards/        # reply va inline klaviaturalar
│   ├── database/         # SQLite ulanishi va barcha repository'lar
│   ├── models/           # (kelajakda kengaytirish uchun, hozircha bo'sh)
│   ├── services/         # obuna tekshiruvi kabi biznes-logika
│   ├── utils/            # logger, wallet ID generator
│   ├── states/           # FSM holatlari
│   ├── config.py
│   ├── loader.py
│   └── main.py
├── logs/
├── .env.example
├── requirements.txt
└── README.md
```

## Ma'lumotlar bazasi jadvallari

`users`, `channels`, `admins`, `withdraws`, `transfers`, `referrals`, `settings`, `broadcast_logs`

## PostgreSQL'ga o'tish

Barcha SQL so'rovlar `app/database/*.py` fayllarida markazlashtirilgan. PostgreSQL'ga
o'tish uchun `app/database/db.py` dagi `aiosqlite` ulanishini `asyncpg` bilan
almashtirish va so'rovlardagi `?` placeholder'larni `$1, $2, ...` formatiga
o'zgartirish kifoya.

## Eslatmalar

- Bot kanal a'zoligini tekshirishi uchun har bir majburiy kanalda **admin** bo'lishi shart.
- `♻ Restart` tugmasi process-level restart qiladi — production muhitda botni
  systemd, pm2 yoki Docker kabi process manager ostida ishga tushirish tavsiya etiladi.
- FSM holatlari hozircha `MemoryStorage`da saqlanadi; ko'p worker/process kerak
  bo'lganda `RedisStorage`ga o'tish tavsiya etiladi.
# yumiolmosbot
