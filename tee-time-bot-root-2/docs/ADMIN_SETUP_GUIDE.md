# Admin Setup Guide — Tee Time Bot

Complete step-by-step instructions for deploying the bot and getting your group online.

---

## Prerequisites

Before you start, you'll need:
- A computer with a web browser (Mac, PC, or phone — no coding required after setup)
- A credit card for Railway.app ($5/month hosting)
- A smartphone with Telegram installed

---

## Phase 1: Create Accounts (20 minutes)

### 1.1 GitHub Account
1. Go to [github.com/signup](https://github.com/signup)
2. Create a free account
3. Verify your email

### 1.2 Railway.app Account
1. Go to [railway.app](https://railway.app)
2. Click "Login" → "Login with GitHub"
3. Authorize Railway to access your GitHub
4. Accept the Terms of Service and Fair Use Policy
5. Upgrade to the Hobby plan ($5/month) under Settings → Billing

### 1.3 Telegram Bot
1. Install Telegram on your phone ([iPhone](https://apps.apple.com/app/telegram-messenger/id686449807) / [Android](https://play.google.com/store/apps/details?id=org.telegram.messenger))
2. Open Telegram, search for **@BotFather**
3. Send: `/newbot`
4. When asked for a name, type: `Tee Time Bot` (or whatever you want)
5. When asked for a username, type: `your_teetime_bot` (must end in "bot", must be unique)
6. BotFather gives you a **token** — it looks like `7123456789:AAH-xxxxxxxxxxxxxxxxxxxxxxxxxxx`
7. **Save this token** — you'll need it in Phase 2

### 1.4 Get Your Telegram Chat ID
1. In Telegram, search for **@userinfobot**
2. Send it any message
3. It replies with your user info including your **Id** (a number like `123456789`)
4. **Save this number** — it's your Chat ID

### 1.5 GolfNow Account
1. Go to [golfnow.com](https://www.golfnow.com)
2. Create an account (or log into your existing one)
3. Go to Account Settings → Payment Methods
4. **Add and save a credit card**
5. **Save your GolfNow email and password** — the bot needs these to log in

### 1.6 Chronogolf Account (Optional — covers 3 more courses)
1. Go to [chronogolf.com](https://www.chronogolf.com)
2. Sign up with email and password
3. Save a credit card if prompted
4. This covers: Bolingbrook, Glen Club, and Preserve at Oak Meadows

### 1.7 OpenWeather API Key (Optional — for weather overlay)
1. Go to [openweathermap.org](https://openweathermap.org/api)
2. Sign up for a free account
3. Go to API Keys and copy your key
4. Free tier gives 1,000 calls/day — more than enough

---

## Phase 2: Deploy the Bot (30 minutes)

### 2.1 Upload Code to GitHub
1. Download the `tee-time-bot.tar.gz` file
2. Extract it on your computer (double-click on Mac, or use 7-Zip on Windows)
3. Go to [github.com/new](https://github.com/new)
4. Repository name: `tee-time-bot`
5. Set to **Private**
6. Click "Create repository"
7. On the next page, click **"uploading an existing file"**
8. Drag and drop ALL the extracted files into the upload area
9. Click "Commit changes"

**Alternative (command line):**
```bash
cd tee-time-bot
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/tee-time-bot.git
git push -u origin main
```

### 2.2 Create Railway Project
1. Go to [railway.app/dashboard](https://railway.app/dashboard)
2. Click **"New Project"**
3. Select **"Deploy from GitHub Repo"**
4. Find and select your `tee-time-bot` repo
5. Railway starts building automatically — this takes 3-5 minutes
6. You'll see build logs in the dashboard

### 2.3 Generate Encryption Key
You need this to securely store user credentials. Run this in any Python environment:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

If you don't have Python installed, you can use Railway's shell:
1. In your Railway project, click on your service
2. Click the **"Shell"** tab (or use `railway shell` from CLI)
3. Run the command above
4. Copy the output

### 2.4 Set Environment Variables
1. In Railway, click on your service
2. Click the **"Variables"** tab
3. Add these variables one at a time:

| Variable | Value | Required? |
|----------|-------|-----------|
| `TELEGRAM_BOT_TOKEN` | `7123456789:AAH-xxx...` (from step 1.3) | Yes |
| `ENCRYPTION_KEY` | `ZmDNcmpX9cZ...` (from step 2.3) | Yes |
| `OPENWEATHER_API_KEY` | Your key (from step 1.7) | Optional |
| `LOG_LEVEL` | `INFO` | Optional |

4. Railway auto-redeploys after adding variables

### 2.5 Generate Public URL
1. In Railway, click your service
2. Click **"Settings"** tab
3. Scroll to **"Networking"** → **"Public Networking"**
4. Click **"Generate Domain"**
5. You'll get a URL like: `https://tee-time-bot-production.up.railway.app`
6. **Save this URL**

### 2.6 Verify Deployment
Open these URLs in your browser:

**Health check:**
```
https://YOUR-APP.up.railway.app/health
```
Expected: `{"status": "ok", ...}`

**API docs (interactive dashboard):**
```
https://YOUR-APP.up.railway.app/docs
```
Expected: A Swagger UI page with all endpoints listed

**Onboarding page (what your friends will see):**
```
https://YOUR-APP.up.railway.app/join
```
Expected: A polished signup guide

---

## Phase 3: Configure the Bot (15 minutes)

### 3.1 Set Up Telegram Webhook
Open this URL in your browser (replace both placeholders):

```
https://api.telegram.org/bot{YOUR_BOT_TOKEN}/setWebhook?url=https://{YOUR-APP}.up.railway.app/telegram/webhook
```

Example:
```
https://api.telegram.org/bot7123456789:AAHxxx/setWebhook?url=https://tee-time-bot-production.up.railway.app/telegram/webhook
```

You should see: `{"ok": true, "result": true, "description": "Webhook was set"}`

### 3.2 Create Your Admin User
1. Go to `https://YOUR-APP.up.railway.app/docs`
2. Find **POST /users**
3. Click "Try it out"
4. Enter this JSON (use your real info):

```json
{
  "name": "Your Name",
  "email": "your@email.com",
  "telegram_chat_id": "123456789",
  "is_admin": true
}
```

5. Click "Execute"
6. **Save the `id` from the response** (e.g., `"a1b2c3d4"`)

### 3.3 Set Your Preferences
1. In the docs page, find **PUT /users/{user_id}/preferences**
2. Enter your user ID from step 3.2
3. Submit this JSON:

```json
{
  "players": 4,
  "preferred_days": ["saturday", "sunday"],
  "earliest_time": "05:00",
  "latest_time": "08:00",
  "max_price": 150,
  "walk_ride": "ride",
  "max_rounds_week": 2,
  "monthly_budget": 600,
  "must_play_courses": [
    "bolingbrook", "mistwood", "preserve_oak",
    "highlands_elgin", "thunderhawk", "schaumburg"
  ],
  "nice_to_have_courses": [
    "cantigny", "cog_hill_123", "harborside",
    "prairie_landing", "bowes_creek"
  ],
  "deal_only_courses": [
    "stonewall", "sanctuary", "glen_club", "cog_hill_4"
  ],
  "alert_threshold": 55,
  "confirm_threshold": 75,
  "autobook_threshold": 90
}
```

### 3.4 Link Your GolfNow Account
1. Find **POST /users/{user_id}/link-account**
2. Enter your user ID
3. Submit:

```json
{
  "platform": "golfnow",
  "username": "your-golfnow-email@email.com",
  "password": "your-golfnow-password"
}
```

Repeat for Chronogolf if you created that account.

### 3.5 Run Your First Scan
1. Find **POST /scan/trigger**
2. Click "Execute"
3. Check your Telegram — alerts should arrive within 1-2 minutes if matching tee times exist
4. If it's off-season or early morning with no availability, you may not see results immediately — that's normal

### 3.6 Update the Onboarding Page
The bot serves a signup page at `/join` that your friends will use. Update the bot username:

1. Open `app/api/onboarding.py`
2. Find `@REPLACE_WITH_BOT_USERNAME`
3. Replace with your bot's actual username (e.g., `@chicago_teetime_bot`)
4. Commit and push to GitHub — Railway auto-redeploys

---

## Phase 4: Add Friends (5 min per person)

### 4.1 Share the Onboarding Link
Send your friends this URL:
```
https://YOUR-APP.up.railway.app/join
```

They'll see a clean step-by-step guide telling them exactly what to do.

### 4.2 After They Message the Bot
Once a friend sends `/start` to your bot and gives you their Chat ID:

1. Go to your API docs page (`/docs`)
2. **POST /users** with their name and Chat ID
3. **PUT /users/{id}/preferences** with their preferred settings
4. **POST /users/{id}/link-account** with their GolfNow credentials (if they want auto-booking)

### 4.3 Verify They're Receiving Alerts
Trigger a test scan and confirm they get a Telegram message. Have them reply **HELP** to verify the command handler is working.

---

## Ongoing Maintenance

### Monitoring
- **Health check:** `https://YOUR-APP.up.railway.app/health`
- **Search analytics:** `https://YOUR-APP.up.railway.app/analytics/searches`
- **Daily digest:** Sent to all admins at 9 PM CT via Telegram

### If Something Breaks
1. Check Railway dashboard → your service → **Deploy Logs** for errors
2. Check the `/analytics/searches` endpoint — if all courses show `status: error`, the scraper may need updating
3. The bot auto-restarts on failure (up to 5 retries)

### Updating the Bot
1. Make changes to the code
2. Push to GitHub: `git push`
3. Railway auto-redeploys in ~2 minutes

### Costs
- Railway.app: ~$5-10/month
- Telegram: Free
- OpenWeather: Free
- GolfNow: Free (you pay green fees for booked rounds)
- **Total: ~$5-10/month**

---

## Quick Reference

| What | URL |
|------|-----|
| Health check | `/health` |
| API docs | `/docs` |
| Friend signup page | `/join` |
| All courses | `/courses` |
| Found tee times | `/slots` |
| Bookings | `/bookings` |
| Active roll calls | `/rollcalls` |
| Search stats | `/analytics/searches` |
| Trigger scan | `POST /scan/trigger` |
| Pause alerts | `POST /alerts/pause` |

---

## Troubleshooting

**Bot isn't sending alerts:**
1. Check `/health` — is it running?
2. Check Railway logs for errors
3. Verify the Telegram webhook is set (`https://api.telegram.org/bot{TOKEN}/getWebhookInfo`)
4. Trigger a manual scan and check `/slots` for results

**Scans return 0 slots:**
1. It may be off-season (courses close Nov-March)
2. Check if the date range has available tee times by visiting GolfNow manually
3. Check `/analytics/searches` for error messages — the course website structure may have changed

**Friend not getting alerts:**
1. Verify their user exists: `GET /users`
2. Check `notification_enabled` is `1`
3. Check for active suppressions: they may have sent STOP or PAUSE
4. Have them message the bot to verify the webhook is working
