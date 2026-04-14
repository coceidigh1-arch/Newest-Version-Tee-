"""
Onboarding page — served at /join
A clean, shareable page your friends open to get started.
"""

from fastapi.responses import HTMLResponse
from app.api.routes import app


ONBOARDING_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Join Tee Time Bot</title>
<link href="https://fonts.googleapis.com/css2?family=Source+Serif+4:wght@400;600&family=DM+Sans:wght@400;500;600&display=swap" rel="stylesheet">
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'DM Sans',sans-serif;background:#f7f9f7;color:#1a3a2a;line-height:1.7}
.hero{background:#1a3a2a;color:#e8f0e8;padding:48px 24px;text-align:center}
.hero h1{font-family:'Source Serif 4',serif;font-size:32px;font-weight:600;margin:0 0 8px}
.hero p{font-size:15px;opacity:0.8;max-width:480px;margin:0 auto}
.container{max-width:600px;margin:0 auto;padding:24px 20px 60px}
.step-card{background:#fff;border:1px solid #dce5dd;border-radius:16px;padding:24px;margin:0 0 16px}
.step-num{display:inline-flex;align-items:center;justify-content:center;width:32px;height:32px;border-radius:50%;background:#1a3a2a;color:#e8f0e8;font-size:14px;font-weight:600;margin:0 8px 8px 0;vertical-align:middle}
.step-card h2{font-size:17px;font-weight:600;display:inline;vertical-align:middle}
.step-card p,.step-card li{font-size:14px;color:#3d5441;margin:8px 0 0;line-height:1.7}
.step-card ul{padding-left:20px}
.step-card li{margin:4px 0}
.app-links{display:flex;gap:10px;margin:12px 0 0}
.app-link{display:inline-block;padding:10px 20px;background:#1a3a2a;color:#e8f0e8;text-decoration:none;border-radius:10px;font-size:13px;font-weight:500;transition:background .15s}
.app-link:hover{background:#2d5a3e}
.code-box{font-family:'SF Mono','Fira Code',monospace;background:#f0f5f1;border:1px solid #dce5dd;border-radius:10px;padding:14px 18px;margin:10px 0;font-size:14px;color:#1a3a2a;word-break:break-all}
.alert-preview{background:#1a3a2a;color:#a8d4b0;border-radius:12px;padding:18px 20px;margin:12px 0;font-family:'SF Mono','Fira Code',monospace;font-size:12px;line-height:1.9;white-space:pre-line}
.cmd-table{width:100%;border-collapse:collapse;margin:12px 0;font-size:13px}
.cmd-table th{text-align:left;font-size:11px;text-transform:uppercase;letter-spacing:0.5px;color:#8a9e8e;padding:6px 8px;border-bottom:1px solid #dce5dd}
.cmd-table td{padding:8px;border-bottom:1px solid #f0f5f1;vertical-align:top}
.cmd-table td:first-child{font-weight:600;white-space:nowrap;color:#1a3a2a}
.badge{display:inline-block;font-size:11px;font-weight:600;padding:2px 10px;border-radius:20px;margin:2px 4px 2px 0}
.badge-low{background:#E1F5EE;color:#0F6E56}
.badge-med{background:#FAEEDA;color:#854F0B}
.badge-high{background:#FCEBEB;color:#A32D2D}
.info-box{background:#E6F1FB;border:1px solid #85B7EB;border-radius:12px;padding:14px 18px;margin:12px 0;font-size:13px;color:#0C447C;line-height:1.6}
.warn-box{background:#FAEEDA;border:1px solid #FAC775;border-radius:12px;padding:14px 18px;margin:12px 0;font-size:13px;color:#633806;line-height:1.6}
.section-label{font-family:'Source Serif 4',serif;font-size:22px;font-weight:600;color:#1a3a2a;margin:32px 0 16px;padding:0 0 8px;border-bottom:2px solid #1a3a2a}
.course-list{columns:2;column-gap:16px;margin:8px 0}
.course-list li{font-size:13px;break-inside:avoid;margin:4px 0}
.faq-q{font-weight:600;font-size:14px;color:#1a3a2a;margin:16px 0 4px}
.faq-a{font-size:13px;color:#3d5441;margin:0 0 12px;padding:0 0 12px;border-bottom:1px solid #f0f5f1}
.footer{text-align:center;padding:24px;font-size:12px;color:#8a9e8e}
</style>
</head>
<body>

<div class="hero">
<h1>Tee Time Bot</h1>
<p>Your group's private golf tee time concierge. 14 Chicago courses monitored 24/7. Instant alerts. One-tap group coordination.</p>
</div>

<div class="container">

<p class="section-label">Get started in 5 minutes</p>

<div class="step-card">
<span class="step-num">1</span>
<h2>Install Telegram</h2>
<p>The bot sends all alerts through Telegram — it's free, instant, and works on every phone.</p>
<div class="app-links">
<a class="app-link" href="https://apps.apple.com/app/telegram-messenger/id686449807" target="_blank">iPhone</a>
<a class="app-link" href="https://play.google.com/store/apps/details?id=org.telegram.messenger" target="_blank">Android</a>
</div>
</div>

<div class="step-card">
<span class="step-num">2</span>
<h2>Find the bot</h2>
<p>Open Telegram and search for:</p>
<div class="code-box">@REPLACE_WITH_BOT_USERNAME</div>
<p>Tap the bot and send:</p>
<div class="code-box">/start</div>
<p>The bot replies with your <strong>Chat ID</strong> — a number like <code>123456789</code>. Copy it.</p>
</div>

<div class="step-card">
<span class="step-num">3</span>
<h2>Send your info to the group admin</h2>
<p>Text or message the admin with:</p>
<ul>
<li>Your <strong>name</strong></li>
<li>Your <strong>Telegram Chat ID</strong> (from step 2)</li>
<li>Your <strong>GolfNow email</strong> (if you have an account)</li>
</ul>
<p>The admin adds you — you'll start getting alerts immediately.</p>
</div>

<div class="step-card">
<span class="step-num">4</span>
<h2>Set up GolfNow (for auto-booking)</h2>
<p>If you want the bot to book tee times on your behalf:</p>
<ul>
<li>Create a free account at <a href="https://www.golfnow.com" target="_blank" style="color:#0F6E56">golfnow.com</a></li>
<li>Go to account settings and <strong>save a credit card</strong></li>
<li>Share your GolfNow email + password with the admin</li>
</ul>
<div class="info-box">
<strong>Your card is safe.</strong> Your card stays on GolfNow's servers — we never store card numbers. The bot just logs into your GolfNow account and clicks "confirm" using your saved card. If you're not comfortable sharing your login, that's fine — the bot will send you a direct booking link instead and you tap to book manually in 30 seconds.
</div>
</div>

<div class="step-card">
<span class="step-num">5</span>
<h2>You're in</h2>
<p>That's it. The bot scans every 10 minutes and sends alerts when it finds tee times matching the group's preferences. Reply to the alert to coordinate with the group.</p>
</div>

<p class="section-label">How alerts work</p>

<div class="step-card">
<h2>Tee time alerts</h2>
<p>When the bot finds a match, you get a message like this:</p>
<div class="alert-preview">⛳ TEE TIME ALERT

📍 Bolingbrook Golf Club
📅 Saturday, June 14, 2026
⏰ 7:40 AM
👥 4 players available
💰 $89/player (ride included)
📊 Score: 92/100
✅ Risk: Low (free cancel 24hr+)

🔗 Book here: [link]</div>
</div>

<div class="step-card">
<h2>Roll calls</h2>
<p>When someone replies <strong>BOOK</strong>, the whole group gets a roll call:</p>
<div class="alert-preview">🏆 ROLL CALL

📍 Bolingbrook Golf Club
📅 Saturday, June 14 at 7:40 AM
💰 $89/player
👥 Need 3 players

Reply IN or OUT</div>
<p>Once enough players reply <strong>IN</strong>, the group gets the booking link. Nobody books until the group is ready.</p>
</div>

<div class="step-card">
<h2>Commands</h2>
<p>Reply to the bot with any of these:</p>
<table class="cmd-table">
<thead><tr><th>Command</th><th>What it does</th></tr></thead>
<tbody>
<tr><td>BOOK</td><td>Start a roll call for the last alert</td></tr>
<tr><td>SKIP</td><td>Dismiss the last alert</td></tr>
<tr><td>IN</td><td>Join the active roll call</td></tr>
<tr><td>OUT</td><td>Decline the roll call</td></tr>
<tr><td>PAUSE</td><td>Pause alerts for 12 hours</td></tr>
<tr><td>STATUS</td><td>Check bot stats</td></tr>
<tr><td>STOP</td><td>Turn off all notifications</td></tr>
<tr><td>RESUME</td><td>Turn notifications back on</td></tr>
<tr><td>HELP</td><td>See the full command list</td></tr>
</tbody>
</table>
</div>

<p class="section-label">Courses we monitor</p>

<div class="step-card">
<p>The bot watches 14 of Chicago's best public courses. Each alert includes the course's cancellation policy so you know exactly what you're committing to.</p>

<p style="font-weight:600;margin:12px 0 4px">Cancellation safety:</p>
<p><span class="badge badge-low">Low risk</span> Free cancel with 24hr notice — safe to book confidently</p>
<p><span class="badge badge-med">Medium risk</span> Cancel conditions apply — check the policy in the alert</p>
<p><span class="badge badge-high">High risk</span> Prepaid, no refund — bot sends a link only, you decide manually</p>

<div class="warn-box">
<strong>The bot never auto-books a high-risk prepaid course.</strong> For courses like Highlands of Elgin, Bowes Creek, and Stonewall Orchard, you always get a link and decide yourself. No surprises on your credit card.
</div>
</div>

<p class="section-label">FAQ</p>

<div class="step-card">
<p class="faq-q">Does this cost me anything?</p>
<p class="faq-a">No. The bot is free. You only pay green fees for rounds you actually book.</p>

<p class="faq-q">Is my credit card safe?</p>
<p class="faq-a">Your card is stored on GolfNow's website, not in our system. The bot logs into your GolfNow account the same way you would on your phone. If you prefer, skip the account linking and book manually via the links in each alert.</p>

<p class="faq-q">What if I book and can't make it?</p>
<p class="faq-a">Every alert includes the course's cancellation policy. Most courses allow free cancel with 24-hour notice. The bot will never auto-book a prepaid/no-refund course.</p>

<p class="faq-q">Can I customize which courses and times I get alerts for?</p>
<p class="faq-a">Yes — ask the admin to update your preferences. You can set different days, time windows, price limits, and course priorities from the rest of the group.</p>

<p class="faq-q">How do I stop getting alerts?</p>
<p class="faq-a">Reply <strong>STOP</strong> to the bot. Reply <strong>RESUME</strong> to start again. Or reply <strong>PAUSE</strong> for a 12-hour break.</p>

<p class="faq-q">What if I don't have a GolfNow account?</p>
<p class="faq-a">You'll still get all the alerts with direct booking links. You just complete the booking yourself by tapping the link. Takes about 30 seconds.</p>
</div>

</div>

<div class="footer">
Tee Time Bot — Chicago A-Group Golf Concierge<br>
Questions? Reply <strong>HELP</strong> to the bot or message the group admin.
</div>

</body>
</html>"""


@app.get("/join", response_class=HTMLResponse)
async def onboarding_page():
    """Shareable onboarding page for new users."""
    return ONBOARDING_HTML


@app.get("/invite", response_class=HTMLResponse)
async def invite_redirect():
    """Alias for /join."""
    return ONBOARDING_HTML
