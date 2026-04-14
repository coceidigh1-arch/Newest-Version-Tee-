# Welcome to Tee Time Bot ⛳

Your friend invited you to a private golf tee time alert system that monitors 14 of Chicago's best courses 24/7 and notifies your group the moment a great tee time opens up.

**What it does:** The bot scans courses like Bolingbrook, Cantigny, Cog Hill, Harborside, Mistwood, and more every 10 minutes. When it finds a tee time that matches the group's preferences (Saturday/Sunday, before 8 AM, 4 players), it sends an instant alert to everyone's phone. You reply with one word and the group locks in the booking.

---

## Setup (5 minutes)

### Step 1: Install Telegram

Download Telegram on your phone if you don't have it already:
- **iPhone:** [App Store](https://apps.apple.com/app/telegram-messenger/id686449807)
- **Android:** [Google Play](https://play.google.com/store/apps/details?id=org.telegram.messenger)

Telegram is a free messaging app. The bot sends all alerts and roll calls through Telegram because it's instant, free, and supports reply commands.

### Step 2: Message the bot

Open Telegram and search for: **@REPLACE_WITH_BOT_USERNAME**

Tap on the bot and send the message:
```
/start
```

The bot will reply with your **Chat ID** — a number that looks like `123456789`. Copy this number.

### Step 3: Send your info to the group admin

Text or message the group admin with:
1. **Your name**
2. **Your Telegram Chat ID** (from Step 2)
3. **Your email** (optional)

The admin will add you to the system. Once you're added, you'll start receiving tee time alerts immediately.

### Step 4: Create a GolfNow account (if you don't have one)

Go to [golfnow.com](https://www.golfnow.com) and create a free account. **Save a credit card** in your account settings under Payment Methods.

This is how the bot books tee times — it logs into your GolfNow account and uses your saved card. Your card number is never stored in our system.

> **Already have a GolfNow account?** Just make sure you have a card saved. That's it.

### Step 5: Share your GolfNow login with the admin

The admin will link your GolfNow account to the bot. Your credentials are encrypted (AES-256) and only used to log in and complete bookings on your behalf.

If you're not comfortable sharing your password, that's fine — the bot will still send you alerts with a direct booking link. You just book manually in 30 seconds by tapping the link.

---

## How it works

### Tee time alerts

When the bot finds a matching tee time, you'll get a Telegram message like this:

```
⛳ TEE TIME ALERT

📍 Bolingbrook Golf Club
📅 Saturday, June 14, 2026
⏰ 7:40 AM
👥 4 players available
💰 $89/player (ride included)
📊 Score: 92/100

🔗 Book here: [link]

Reply:
✅ BOOK — Start the roll call
⏭ SKIP — Not interested
⏸ PAUSE — Stop alerts today
```

### Roll calls

When someone replies **BOOK**, the bot sends a roll call to the whole group:

```
🏆 ROLL CALL

📍 Bolingbrook Golf Club
📅 Saturday, June 14 at 7:40 AM
💰 $89/player
👥 Need 3 players

Reply:
✅ IN — Count me in
❌ OUT — Can't make it
```

Once enough players confirm, the bot sends everyone the booking link (or books automatically if the group has that enabled).

### Commands you can use

Just reply to the bot with any of these:

| Command | What it does |
|---------|-------------|
| **BOOK** | Start a roll call for the last alert |
| **SKIP** | Dismiss the last alert |
| **IN** | Join an active roll call |
| **OUT** | Decline an active roll call |
| **PAUSE** | Pause all alerts for 12 hours |
| **PAUSE [course]** | Pause alerts for one course (e.g., "PAUSE Bolingbrook") |
| **STATUS** | Check if the bot is running and see stats |
| **STOP** | Turn off all notifications |
| **RESUME** | Turn notifications back on |
| **HELP** | See the command list |

---

## Courses we're monitoring

The bot watches these 14 courses (your admin may customize this list):

### Must-play (highest priority alerts)
- Bolingbrook Golf Club
- Mistwood Golf Club
- The Preserve at Oak Meadows
- Highlands of Elgin
- Thunderhawk Golf Club
- Schaumburg Golf Club

### Nice to have
- Cantigny Golf Club (27 holes, best public in Chicago)
- Cog Hill #1/2/3 (4 courses, dynamic pricing)
- Harborside International (Port & Starboard, closest to city)
- Prairie Landing
- Bowes Creek CC

### Deal only (alerts when price is right)
- Stonewall Orchard (top 3 in IL, but far and pricey)
- The Sanctuary (far, very open and flat)
- The Glen Club (expensive at full price)
- Cog Hill #4 Dubsdread (#1 rated in IL)

---

## Important: Cancellation policies

Not all courses let you cancel for free. The bot knows each course's policy and handles it:

**Low risk (free cancel 24hr+):** Bolingbrook, Harborside, Glen Club, Schaumburg, Prairie Landing, Sanctuary — the bot can auto-book these confidently.

**Medium risk (cancel with conditions):** Cantigny, Cog Hill 1/2/3, Thunderhawk, Mistwood, Preserve at Oak Meadows — cancel is free 24-48hr out, but no-show fees apply.

**High risk (prepaid, no refund):** Highlands of Elgin, Bowes Creek, Stonewall Orchard, Cog Hill #4 — the bot will ONLY send you a link for these. No auto-booking. You decide manually.

**Bottom line:** The bot never books a high-risk prepaid course without you manually tapping the link and confirming. Your money is protected.

---

## Your preferences

The admin sets default group preferences, but you can customize yours. Want alerts on Fridays too? Only care about courses under $100? Prefer walking? The admin can update your settings through the system, or you can request changes anytime.

**Default settings:**
- Days: Saturday & Sunday
- Time: Before 8:00 AM
- Players: 4
- Max price: $150/player
- Ride preferred

---

## FAQ

**Q: Does this cost me anything?**
A: No. The bot is free. You only pay for the golf rounds you actually book.

**Q: Is my credit card safe?**
A: Your card is saved on GolfNow's website (not in our system). The bot just logs into your GolfNow account to complete bookings. If you prefer, you can skip account linking and just book manually via the links the bot sends.

**Q: What if I can't make it to a round that was booked?**
A: Check the cancellation policy for that course (included in every alert). Most courses allow free cancellation with 24-hour notice. For prepaid courses, you'd need to find a replacement player or use the rain check.

**Q: How do I stop getting alerts?**
A: Reply **STOP** to the bot. Reply **RESUME** to start again. You can also **PAUSE** for 12 hours if you just need a break.

**Q: Can I be in multiple golf groups?**
A: Currently one group per bot instance. If you want separate groups with different preferences, the admin would set up a second bot.

---

## Questions?

Message the group admin or reply **HELP** to the bot anytime.

See you on the course. 🏌️
