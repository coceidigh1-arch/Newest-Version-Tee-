# Tee Time Bot — Chicago A-Group Golf Course Monitor

A self-hosted tee time search, alert, and booking agent for 14 premium Chicago-area golf courses. Runs 24/7 on Railway.app, sends push notifications via Telegram, and supports multi-user profiles with per-person booking platform accounts.

## Features

- **14-course monitoring** across 4 booking platforms (GolfNow, Chronogolf, ForeUP, custom)
- **Smart scoring** (0–100) based on course priority, day, time, price, and player count
- **Multi-user profiles** — each friend links their own GolfNow/Chronogolf account
- **Roll call** — group coordination before any booking is confirmed
- **Auto-book** via Playwright on GolfNow/Chronogolf (using saved cards on platform)
- **Deep link alerts** for custom booking sites (Cog Hill, Mistwood, Highlands, Bowes Creek)
- **Cancellation-aware** — risk tier per course prevents auto-booking on prepaid/no-refund courses
- **Telegram notifications** with BOOK/SKIP/PAUSE reply commands
- **Budget tracking** — monthly spend limits and weekly round caps
- **Weather overlay** — suppress alerts for rainy days
- **Dynamic scan frequency** — surge mode when cancellations are detected
- **Duplicate suppression** — SHA-256 slot deduplication
- **CAPTCHA fallback** — graceful downgrade to deep link if CAPTCHA detected

## Quick Start (Railway.app)

1. Fork this repo
2. Create a Railway project and connect your GitHub repo
3. Set environment variables (see `.env.example`)
4. Deploy — Railway auto-builds from the Dockerfile
5. Create a Telegram bot via @BotFather, set the token in env vars
6. Open the API at `https://your-app.railway.app/docs` to configure users and courses

## Architecture

```
┌─────────────────────────────────────────────┐
│              Scheduler (APScheduler)         │
│         Every 5-15 min, dynamic by time      │
└────────────────────┬────────────────────────┘
                     ▼
┌─────────────────────────────────────────────┐
│             Scraper Engine                   │
│  GolfNow │ Chronogolf │ ForeUP │ Custom     │
└────────────────────┬────────────────────────┘
                     ▼
┌─────────────────────────────────────────────┐
│          Score & Match Engine                │
│  0-100 scoring → dedup → route action        │
└────────────────────┬────────────────────────┘
                     ▼
┌──────────┬─────────────┬────────────────────┐
│  IGNORE  │    ALERT    │   BOOK / CONFIRM   │
│  (log)   │ (Telegram)  │ (Roll Call → Book) │
└──────────┴─────────────┴────────────────────┘
                     ▼
┌─────────────────────────────────────────────┐
│         FastAPI (REST endpoints)             │
│  /users /courses /preferences /bookings      │
│  /rollcall /health                           │
└─────────────────────────────────────────────┘
```

## Tech Stack

- Python 3.12+
- FastAPI + Uvicorn
- SQLite (via aiosqlite)
- Playwright (browser automation)
- APScheduler (cron scheduling)
- httpx (async HTTP)
- BeautifulSoup4 (HTML parsing)
- python-telegram-bot (notifications)
- cryptography (Fernet encryption for credentials)

## Environment Variables

See `.env.example` for the full list. Key ones:
- `TELEGRAM_BOT_TOKEN` — from @BotFather
- `ENCRYPTION_KEY` — generated via `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`
- `DATABASE_URL` — defaults to `sqlite:///data/teebot.db`
