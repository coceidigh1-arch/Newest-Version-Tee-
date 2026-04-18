"""
Dashboard — serves at /dashboard
Self-contained single-page dark-mode dashboard. All styling and behaviour live
inline so the whole thing ships as one HTTP response with no build step.
"""
from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter()


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    return _HTML


_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="theme-color" content="#0a0d0c">
<meta name="color-scheme" content="dark">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="description" content="Live tee time scanner for Chicago's best public golf courses. See every open time for the next 7 days.">
<meta property="og:title" content="Tee Time Bot — Live Chicago tee times">
<meta property="og:description" content="Live tee time scanner for Chicago's best courses. See every open time for the next 7 days.">
<meta property="og:type" content="website">
<meta name="twitter:card" content="summary">
<title>Tee Time Bot</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
:root{
  --bg:#0a0d0c;
  --bg-soft:#0f1413;
  --surface:#12181a;
  --surface-2:#151d1f;
  --surface-hi:#1a2427;
  --border:#1e2a2c;
  --border-2:#2a393c;
  --text:#e7ecea;
  --text-2:#9caaa5;
  --text-3:#60706c;
  --accent:#6ee7a0;
  --accent-hover:#8bf0b4;
  --accent-dim:rgba(110,231,160,0.12);
  --accent-text:#07110c;
  --warn:#f59e0b;
  --warn-dim:rgba(245,158,11,0.12);
  --danger:#f87171;
  --danger-dim:rgba(248,113,113,0.12);
  --info:#60a5fa;
  --radius:14px;
  --radius-sm:10px;
  --radius-xs:8px;
}
*{box-sizing:border-box;margin:0;padding:0}
html,body{height:100%}
body{
  font-family:'Inter',system-ui,-apple-system,Segoe UI,sans-serif;
  background:var(--bg);
  color:var(--text);
  font-size:14px;
  line-height:1.5;
  -webkit-font-smoothing:antialiased;
  -moz-osx-font-smoothing:grayscale;
  text-rendering:optimizeLegibility;
}
a{color:var(--accent);text-decoration:none}
a:hover{text-decoration:underline}
button{font-family:inherit}
::selection{background:var(--accent-dim);color:var(--text)}

.app{
  max-width:640px;
  margin:0 auto;
  min-height:100vh;
  padding-bottom:48px;
}

/* Header */
.header{
  display:flex;
  align-items:center;
  justify-content:space-between;
  gap:12px;
  padding:20px 20px 12px;
}
.brand{display:flex;align-items:center;gap:10px;min-width:0}
.brand-mark{
  width:30px;height:30px;
  border-radius:9px;
  background:linear-gradient(135deg,#183828,#0a2416);
  border:1px solid var(--border-2);
  display:flex;align-items:center;justify-content:center;
  font-size:15px;flex-shrink:0;
}
.brand-text{min-width:0}
.brand h1{
  font-size:15px;font-weight:600;
  letter-spacing:-0.01em;
  color:var(--text);
  white-space:nowrap;
}
.brand-sub{
  display:flex;align-items:center;gap:6px;
  font-size:11px;color:var(--text-3);
  margin-top:2px;letter-spacing:0.01em;
}
.live-dot{
  width:6px;height:6px;border-radius:50%;
  background:var(--accent);
  box-shadow:0 0 8px rgba(110,231,160,0.5);
  animation:pulse 2.4s ease-in-out infinite;
}
.live-dot.offline{background:var(--text-3);box-shadow:none;animation:none}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:0.55}}
.icon-btn{
  width:38px;height:38px;
  border-radius:10px;
  border:1px solid var(--border);
  background:var(--surface);
  color:var(--text-2);
  cursor:pointer;
  display:flex;align-items:center;justify-content:center;
  transition:all .15s ease;
  flex-shrink:0;
}
.icon-btn:hover:not(:disabled){border-color:var(--border-2);color:var(--text);background:var(--surface-2)}
.icon-btn:disabled{opacity:0.4;cursor:not-allowed}
.icon-btn.loading svg{animation:spin 0.9s linear infinite}
@keyframes spin{to{transform:rotate(360deg)}}

/* Tabs */
.tabs{
  display:flex;
  gap:2px;
  padding:0 14px;
  border-bottom:1px solid var(--border);
  overflow-x:auto;
  scrollbar-width:none;
  -webkit-overflow-scrolling:touch;
  position:sticky;top:0;
  background:var(--bg);
  z-index:30;
}
.tabs::-webkit-scrollbar{display:none}
.tab{
  padding:12px 12px 11px;
  background:none;border:none;
  color:var(--text-3);
  font-size:13px;font-weight:500;
  cursor:pointer;
  white-space:nowrap;
  border-bottom:2px solid transparent;
  margin-bottom:-1px;
  transition:color .12s;
  display:flex;align-items:center;gap:6px;
}
.tab:hover{color:var(--text-2)}
.tab.active{color:var(--text);border-bottom-color:var(--accent)}
.tab-badge{
  background:var(--warn);color:#0a0d0c;
  font-size:10px;font-weight:700;
  padding:1px 6px;border-radius:20px;
  line-height:1.4;
}

/* Content */
.content{padding:18px 16px 8px}

.section-title{font-size:19px;font-weight:600;letter-spacing:-0.01em;color:var(--text)}
.section-sub{font-size:13px;color:var(--text-2);margin-top:4px;line-height:1.55}
.section-head{margin-bottom:16px}
.section + .section{margin-top:28px}

/* Cards */
.card{
  background:var(--surface);
  border:1px solid var(--border);
  border-radius:var(--radius);
  padding:14px 16px;
  transition:border-color .15s ease,background .15s ease;
  animation:fadeUp .32s ease both;
}
@keyframes fadeUp{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:translateY(0)}}
.card + .card{margin-top:8px}
.card:hover{border-color:var(--border-2);background:var(--surface-2)}

/* Slot card */
.slot{
  display:grid;
  grid-template-columns:auto 1fr auto;
  align-items:center;
  gap:14px;
}
.slot-time{
  font-variant-numeric:tabular-nums;
  font-size:18px;
  font-weight:600;
  letter-spacing:-0.02em;
  color:var(--text);
  min-width:74px;
}
.slot-info{display:flex;flex-direction:column;gap:3px;min-width:0}
.slot-course{
  font-size:13.5px;font-weight:500;color:var(--text);
  overflow:hidden;text-overflow:ellipsis;white-space:nowrap;
}
.slot-meta{
  display:flex;gap:8px;
  font-size:12px;color:var(--text-2);
  align-items:center;flex-wrap:wrap;
  font-variant-numeric:tabular-nums;
}
.slot-meta > * + *::before{content:"·";margin-right:8px;color:var(--text-3)}
.slot-price{color:var(--text);font-weight:500}
.slot-price.hot{color:var(--warn)}
.slot-price.good{color:var(--accent)}
.slot-price.prem{color:var(--danger)}
.slot-action{
  background:var(--accent);
  color:var(--accent-text);
  padding:8px 14px;
  border-radius:10px;
  font-size:12.5px;
  font-weight:600;
  transition:background .15s,transform .15s;
  white-space:nowrap;
  flex-shrink:0;
}
.slot-action:hover{background:var(--accent-hover);text-decoration:none;transform:translateY(-1px)}

/* Tier + deal tags */
.tier{font-size:10px;font-weight:600;padding:1px 6px;border-radius:4px;vertical-align:middle;margin-left:6px;letter-spacing:0.02em}
.tier-ap{color:#fbbf24;background:rgba(251,191,36,0.1);border:1px solid rgba(251,191,36,0.28)}
.tier-a{color:#6ee7a0;background:rgba(110,231,160,0.08);border:1px solid rgba(110,231,160,0.28)}
.tier-am{color:#60a5fa;background:rgba(96,165,250,0.08);border:1px solid rgba(96,165,250,0.28)}
.tier-b{color:#9ba8a4;background:rgba(155,168,164,0.08);border:1px solid rgba(155,168,164,0.28)}
.deal{font-size:10px;font-weight:600;padding:2px 7px;border-radius:20px;letter-spacing:0.02em;margin-left:2px}
.deal-hot{color:var(--warn);background:var(--warn-dim)}
.deal-good{color:var(--accent);background:var(--accent-dim)}
.deal-prem{color:var(--danger);background:var(--danger-dim)}

/* Day header */
.day-header{
  display:flex;align-items:baseline;justify-content:space-between;
  gap:10px;margin:22px 0 10px;
}
.day-header:first-child{margin-top:4px}
.day-title{display:flex;align-items:baseline;gap:8px;min-width:0;flex-wrap:wrap}
.day-date{font-size:15px;font-weight:600;color:var(--text);letter-spacing:-0.01em}
.day-count{font-size:12px;color:var(--text-3);font-weight:400}
.day-weather{
  display:inline-flex;align-items:center;gap:6px;
  font-size:12px;color:var(--text-2);
  padding:3px 9px;border-radius:20px;
  background:var(--surface);border:1px solid var(--border);
  font-variant-numeric:tabular-nums;flex-shrink:0;
}
.day-weather.bad{color:var(--danger);background:var(--danger-dim);border-color:rgba(248,113,113,0.2)}

/* Empty / loading */
.empty{
  text-align:center;
  padding:36px 20px;
  color:var(--text-2);
  font-size:13px;
  line-height:1.6;
  background:var(--surface);
  border:1px dashed var(--border-2);
  border-radius:var(--radius);
}
.empty-icon{font-size:24px;margin-bottom:10px;opacity:0.8}
.empty-title{font-size:14px;color:var(--text);margin-bottom:4px;font-weight:500}
.empty-hint{color:var(--text-3)}
.empty-inline{
  font-size:12px;color:var(--text-3);
  text-align:center;padding:14px;
  background:var(--surface);
  border:1px dashed var(--border);
  border-radius:var(--radius-sm);
}
.skeleton{
  border-radius:var(--radius);
  background:linear-gradient(90deg,var(--surface) 0%,var(--surface-hi) 50%,var(--surface) 100%);
  background-size:200% 100%;
  animation:shimmer 1.3s ease-in-out infinite;
  height:68px;
}
.skeleton + .skeleton{margin-top:8px}
@keyframes shimmer{from{background-position:200% 0}to{background-position:-200% 0}}

/* Banner */
.banner{
  padding:12px 14px;
  border-radius:var(--radius-sm);
  margin-bottom:12px;
  font-size:13px;line-height:1.5;
  display:flex;gap:10px;align-items:flex-start;
}
.banner-icon{font-size:16px;flex-shrink:0;line-height:1.3}
.banner-body{flex:1;min-width:0}
.banner.warn{background:var(--warn-dim);border:1px solid rgba(245,158,11,0.28);color:#fcd34d}
.banner.info{background:var(--accent-dim);border:1px solid rgba(110,231,160,0.25);color:#a7f3c4}
.banner.err{background:var(--danger-dim);border:1px solid rgba(248,113,113,0.28);color:#fca5a5}

/* Form primitives */
.field{margin-bottom:12px}
.label{
  font-size:10.5px;color:var(--text-3);font-weight:500;
  letter-spacing:0.06em;text-transform:uppercase;
  margin-bottom:6px;display:block;
}
.input,.select{
  width:100%;
  padding:11px 12px;
  font-family:inherit;font-size:14px;
  background:var(--surface);color:var(--text);
  border:1px solid var(--border);
  border-radius:var(--radius-sm);
  -webkit-appearance:none;appearance:none;
  transition:border-color .15s;
}
.input::placeholder{color:var(--text-3)}
.select{
  background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath d='M3 4.5l3 3 3-3' stroke='%239caaa5' stroke-width='1.6' fill='none' stroke-linecap='round' stroke-linejoin='round'/%3E%3C/svg%3E");
  background-repeat:no-repeat;
  background-position:right 12px center;
  padding-right:34px;
  cursor:pointer;
}
.input:focus,.select:focus{border-color:var(--border-2);outline:none}
.row{display:flex;gap:8px}
.row > *{flex:1;min-width:0}

/* Buttons */
.button{
  display:inline-flex;align-items:center;justify-content:center;gap:6px;
  padding:11px 16px;
  background:var(--accent);
  color:var(--accent-text);
  border:none;
  border-radius:var(--radius-sm);
  font-size:13px;font-weight:600;
  cursor:pointer;
  transition:background .15s,transform .1s;
  -webkit-appearance:none;appearance:none;
}
.button:hover:not(:disabled){background:var(--accent-hover)}
.button:active:not(:disabled){transform:scale(0.98)}
.button:disabled{opacity:0.4;cursor:not-allowed}
.button.secondary{background:var(--surface-2);color:var(--text);border:1px solid var(--border)}
.button.secondary:hover:not(:disabled){background:var(--surface-hi);border-color:var(--border-2)}
.button.ghost{background:transparent;color:var(--text-2);border:1px solid var(--border)}
.button.ghost:hover:not(:disabled){color:var(--text);border-color:var(--border-2)}
.button.danger-ghost{background:transparent;color:var(--danger);border:1px solid rgba(248,113,113,0.3);font-weight:500}
.button.danger-ghost:hover:not(:disabled){background:var(--danger-dim)}
.button.full{width:100%}
.button.sm{padding:7px 12px;font-size:12px}

/* Segmented control (e.g., players) */
.segmented{
  display:flex;
  background:var(--surface);
  border:1px solid var(--border);
  border-radius:var(--radius-sm);
  padding:3px;gap:2px;
}
.segmented button{
  flex:1;background:none;border:none;
  padding:8px 4px;
  color:var(--text-2);
  font-size:13px;font-weight:500;
  cursor:pointer;
  border-radius:7px;
  transition:all .12s;
}
.segmented button.active{background:var(--surface-hi);color:var(--text)}
.segmented button:hover:not(.active){color:var(--text)}

/* Connect / onboarding steps */
.step{
  display:flex;gap:12px;
  padding:14px 16px;
  background:var(--surface);
  border:1px solid var(--border);
  border-radius:var(--radius);
}
.step + .step{margin-top:10px}
.step-num{
  flex-shrink:0;
  width:26px;height:26px;border-radius:50%;
  background:var(--surface-hi);color:var(--text);
  display:flex;align-items:center;justify-content:center;
  font-size:12px;font-weight:600;
}
.step-body{flex:1;min-width:0}
.step-title{font-size:14px;font-weight:500;color:var(--text);margin-bottom:3px}
.step-hint{font-size:12.5px;color:var(--text-2);line-height:1.55}
.kbd{
  font-family:'JetBrains Mono',Menlo,monospace;
  font-size:12px;color:var(--text);
  padding:2px 6px;border-radius:4px;
  background:var(--surface-hi);border:1px solid var(--border);
}

/* Course list row */
.course-row{
  display:flex;align-items:center;justify-content:space-between;gap:12px;
  padding:12px 14px;
  background:var(--surface);border:1px solid var(--border);
  border-radius:var(--radius-sm);
  cursor:pointer;
  transition:all .15s;
}
.course-row + .course-row{margin-top:6px}
.course-row:hover{border-color:var(--border-2);background:var(--surface-2)}
.course-name{font-size:13.5px;font-weight:500;color:var(--text)}
.course-meta{font-size:11px;color:var(--text-3);margin-top:2px;font-variant-numeric:tabular-nums}
.platform-chip{
  font-size:10px;font-weight:500;
  padding:2px 8px;border-radius:20px;
  color:var(--text-2);
  background:var(--surface-hi);border:1px solid var(--border);
  letter-spacing:0.02em;
}

/* Active alerts row */
.list-row{
  display:flex;justify-content:space-between;align-items:center;gap:10px;
  padding:10px 14px;background:var(--surface);
  border:1px solid var(--border);border-radius:var(--radius-sm);
}
.list-row + .list-row{margin-top:6px}
.list-title{font-size:13px;font-weight:500;color:var(--text)}
.list-meta{font-size:11.5px;color:var(--text-3);margin-top:2px}

/* Footer */
.footer{
  text-align:center;
  padding:24px 16px 28px;
  font-size:11px;
  color:var(--text-3);
  letter-spacing:0.02em;
}

/* Small screens */
@media (max-width:460px){
  .slot{gap:12px}
  .slot-time{font-size:17px;min-width:66px}
  .slot-action{padding:7px 12px;font-size:12px}
  .content{padding:16px 14px 8px}
  .header{padding:18px 14px 10px}
  .tabs{padding:0 10px}
  .tab{padding:12px 10px 11px;font-size:12.5px}
}
@media (max-width:360px){
  .slot{grid-template-columns:auto 1fr}
  .slot-action{grid-column:1 / -1;text-align:center;padding:9px;width:100%}
}
</style>
</head>
<body>
<div id="app" class="app"></div>
<script>
var API = location.origin;

/* ==========================================================================
   Course directory
   The course catalog is hardcoded here so the dashboard is fully self-contained
   (no extra RPC to render a selector). Keep this in sync with app/models/courses.py
   if courses are added or removed.
   Fields: n=name, t=tier, d=distance (mi), adv=advance (days), s=platform,
           u=booking URL, avg=typical price ($)
   ========================================================================== */
var C = {
  bolingbrook:{n:"Bolingbrook GC",t:"A+",d:34,adv:14,s:"golfnow",u:"https://www.golfnow.com/tee-times/facility/734-bolingbrook-golf-club/search",avg:92},
  harborside:{n:"Harborside Intl",t:"A+",d:15,adv:21,s:"golfnow",u:"https://www.golfnow.com/tee-times/facility/1108-harborside-international-golf-center-port-course/search",avg:85},
  stonewall:{n:"Stonewall Orchard",t:"A+",d:45,adv:7,s:"golfnow",u:"https://www.golfnow.com/tee-times/facility/11392-stonewall-orchard-golf-club/search",avg:95},
  thunderhawk:{n:"Thunderhawk GC",t:"A+",d:50,adv:30,s:"golfnow",u:"https://www.golfnow.com/tee-times/facility/7739-thunderhawk-golf-course/search",avg:85},
  schaumburg:{n:"Schaumburg GC",t:"A",d:30,adv:7,s:"golfnow",u:"https://www.golfnow.com/tee-times/facility/727-schaumburg-golf-club/search",avg:85},
  preserve_oak:{n:"Preserve at Oak Meadows",t:"A+",d:25,adv:28,s:"chronogolf",u:"https://www.chronogolf.com/club/oak-meadows-golf-course#teetimes",avg:80},
  glen_club:{n:"The Glen Club",t:"A+",d:20,adv:7,s:"ezlinks",u:"https://theglenclub.ezlinksgolf.com/index.html#/search",avg:180},
  highlands_elgin:{n:"Highlands of Elgin",t:"A",d:40,adv:7,s:"proshop_teetimes",u:"https://booking.proshopteetimes.com/SelectPlayers.aspx?CourseID=95",avg:77},
  bowes_creek:{n:"Bowes Creek CC",t:"A",d:40,adv:7,s:"proshop_teetimes",u:"https://booking.proshopteetimes.com/SelectPlayers.aspx?CourseID=94",avg:70},
  cantigny:{n:"Cantigny Golf",t:"A+",d:30,adv:14,s:"whoosh",u:"https://app.whoosh.io/patron/club/cantigny-golf-course/agenda/golf-course/",avg:120},
  cog_hill_123:{n:"Cog Hill 1-2-3",t:"A",d:28,adv:14,s:"foreup",u:"https://foreupsoftware.com/index.php/booking/a/22487/11#/teetimes",avg:75},
  cog_hill_4:{n:"Cog Hill 4 Dubsdread",t:"A+",d:28,adv:14,s:"foreup",u:"https://foreupsoftware.com/index.php/booking/a/22487/11#/teetimes",avg:110},
  mistwood:{n:"Mistwood GC",t:"A+",d:35,adv:10,s:"cps_golf",u:"https://mistwood.cps.golf/onlineresweb/search-teetime?TeeOffTimeMin=0&TeeOffTimeMax=23",avg:90},
  prairie_landing:{n:"Prairie Landing",t:"A",d:35,adv:7,s:"golfback",u:"https://golfback.com/#/course/dba9546a-1cdf-4c55-8abb-e8bfcb7c6c84",avg:85},
  arboretum:{n:"Arboretum GC",t:"A",d:35,adv:7,s:"golfnow",u:"https://www.golfnow.com/tee-times/facility/6171-the-arboretum-golf-club/search",avg:55},
  balmoral_woods:{n:"Balmoral Woods CC",t:"A",d:36,adv:7,s:"chronogolf",u:"https://www.chronogolf.com/club/5552/widget?medium=widget&source=club",avg:55},
  bartlett_hills:{n:"Bartlett Hills GC",t:"A",d:34,adv:7,s:"direct",u:"https://www.bartletthills.com/teetimes/",avg:45},
  bridges_poplar:{n:"Bridges of Poplar Creek",t:"A",d:35,adv:7,s:"ezlinks",u:"https://poplarcreekccpp.ezlinksgolf.com/index.html#/search",avg:55},
  broken_arrow:{n:"Broken Arrow GC",t:"A",d:37,adv:7,s:"teeitup",u:"https://broken-arrow-golf-club.book.teeitup.com/?course=7300",avg:40},
  chevy_chase:{n:"Chevy Chase CC",t:"A",d:32,adv:7,s:"direct",u:"https://www.traditionsatchevychase.com/tee-time/",avg:50},
  coyote_run:{n:"Coyote Run GC",t:"B+",d:27,adv:7,s:"golfnow",u:"https://www.golfnow.com/tee-times/facility/700-coyote-run-golf-course-il/search",avg:55},
  deerfield:{n:"Deerfield GC",t:"A",d:30,adv:7,s:"golfnow",u:"https://www.golfnow.com/tee-times/facility/5435-deerfield-golf-club/search",avg:39},
  fox_run:{n:"Fox Run GC",t:"A",d:29,adv:7,s:"direct",u:"https://www.foxrungolflinks.com/tee-times/",avg:45},
  foxford_hills:{n:"Foxford Hills GC",t:"A+",d:45,adv:7,s:"golfnow",u:"https://www.golfnow.com/tee-times/facility/841-foxford-hills-golf-club/search",avg:50},
  george_dunne:{n:"George Dunne National",t:"A",d:25,adv:7,s:"golfnow",u:"https://www.golfnow.com/tee-times/facility/3316-george-w-dunne-national-golf-course/search",avg:54},
  green_garden:{n:"Green Garden CC",t:"A",d:39,adv:7,s:"direct",u:"https://www.greengardencc.com/teetimes/",avg:50},
  hilldale:{n:"Hilldale GC",t:"A",d:35,adv:7,s:"teeitup",u:"https://hilldale-golf-club.book.teeitup.com/?course=4855",avg:45},
  links_carillon:{n:"Links at Carillon",t:"A",d:34,adv:7,s:"ezlinks",u:"https://carillon.ezlinksgolf.com/index.html#/search",avg:60},
  lost_marsh:{n:"Lost Marsh GC",t:"A",d:25,adv:7,s:"direct",u:"https://www.lostmarshgolf.com/teetimes/",avg:55},
  makray:{n:"Makray Memorial",t:"A",d:38,adv:7,s:"golfnow",u:"https://www.golfnow.com/tee-times/facility/847-makray-memorial-golf-club/search",avg:80},
  pine_meadow:{n:"Pine Meadow GC",t:"A",d:41,adv:7,s:"golfnow",u:"https://www.golfnow.com/tee-times/facility/3300-pine-meadow/search",avg:60},
  prairie_bluff:{n:"Prairie Bluff GC",t:"A-",d:36,adv:7,s:"chronogolf",u:"https://www.chronogolf.com/club/prairie-bluff-golf-club",avg:65},
  ruffled_feathers:{n:"Ruffled Feathers GC",t:"A",d:28,adv:7,s:"golfnow",u:"https://www.golfnow.com/tee-times/facility/945-ruffled-feathers-golf-club/search",avg:70},
  st_andrews:{n:"St. Andrews GC",t:"A",d:37,adv:7,s:"teeitup",u:"https://st-andrews-golf-club-chicago-v2.book.teeitup.com/?course=3299,5038",avg:50},
  seven_bridges:{n:"Seven Bridges GC",t:"A+",d:28,adv:7,s:"golfnow",u:"https://www.golfnow.com/tee-times/facility/827-seven-bridges-golf-club/search",avg:77},
  sunset_valley:{n:"Sunset Valley GC",t:"B+",d:25,adv:7,s:"foreup",u:"https://foreupsoftware.com/index.php/booking/21000/6510#/teetimes",avg:50},
  waters_edge:{n:"Waters Edge GC",t:"A",d:20,adv:7,s:"golfnow",u:"https://www.golfnow.com/tee-times/facility/2408-waters-edge-golf-club/search",avg:55},
  sanctuary:{n:"Sanctuary GC",t:"A",d:35,adv:7,s:"foreup",u:"https://foreupsoftware.com/index.php/booking/21043/6838#teetimes",avg:75}
};
var sorted = Object.entries(C).sort(function(a,b){return a[1].n.localeCompare(b[1].n)});
var scanN = sorted.length;

/* ==========================================================================
   State
   ========================================================================== */
var P = {
  tab:"now",
  health:null, scanning:false,
  weather:{},
  // Now tab
  nowSlots:[], nowLimit:10,
  coursePick:"", courseWeek:null, courseWeekDays:7,
  players:1, timeMin:"05:00", timeMax:"19:00",
  // All week tab
  slots:[], course:"",
  // Search tab
  searchSlots:[], searchCourse:"", date:"", searchLimit:30,
  // Alerts
  webAlerts:[], webMatches:[], alertCourse:"",
  alertEmail:"", alertTimeMin:"05:00", alertTimeMax:"14:00",
  alertDateFrom:"", alertDateTo:"", alertPlayers:1, alertMsg:null,
  // Snipe
  snipes:[], sc:"bolingbrook", sd:"sat", st:"07:00", sp:4, sm:null,
  // Connect
  cn:"", ce:"", ct:"", cmsg:null,
  // Meta
  loading:false, sessionId:""
};

/* ==========================================================================
   Utility helpers
   ========================================================================== */
function today(){return new Date().toISOString().split("T")[0]}
function nsat(){var d=new Date();d.setDate(d.getDate()+((6-d.getDay())%7||7));return d.toISOString().split("T")[0]}
function nowTime(){var d=new Date();return String(d.getHours()).padStart(2,"0")+":"+String(d.getMinutes()).padStart(2,"0")}
function fd(d){if(!d)return "";return new Date(d+"T12:00:00").toLocaleDateString("en-US",{weekday:"short",month:"short",day:"numeric"})}
function ft(t){
  if(!t||t.indexOf(":")<0)return t||"";
  var p=t.split(":");var h=parseInt(p[0]);
  var ap=h>=12?"PM":"AM";var h12=h===0?12:h>12?h-12:h;
  return h12+":"+p[1]+" "+ap;
}
function tcCls(t){return t==="A+"?"tier-ap":t==="A"?"tier-a":t==="A-"?"tier-am":"tier-b"}
function priceBand(p,cid){
  var c=C[cid];if(!c||!c.avg||!p||p<=0)return null;
  var r=p/c.avg;
  if(r<=0.70)return "hot";
  if(r<=0.85)return "good";
  if(r>=1.15)return "prem";
  return null;
}
function priceTag(p,cid){
  var b=priceBand(p,cid);
  if(b==="hot")return " <span class=\"deal deal-hot\">HOT DEAL</span>";
  if(b==="good")return " <span class=\"deal deal-good\">DEAL</span>";
  if(b==="prem")return " <span class=\"deal deal-prem\">PREMIUM</span>";
  return "";
}
function escapeHtml(s){return String(s==null?"":s).replace(/[&<>"']/g,function(c){return {"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;"}[c]})}

/* API helper — injects user token when available, returns null on failure */
function api(u,o){
  var opts=o||{};
  var h=Object.assign({},opts.headers||{});
  var tok=localStorage.getItem("tbot_tok");
  if(tok && !h["X-User-Token"]) h["X-User-Token"]=tok;
  opts.headers=h;
  return fetch(API+u,opts).then(function(r){return r.json()}).catch(function(){return null});
}

/* ==========================================================================
   Fetchers
   ========================================================================== */
function loadWeather(dates){
  var dl=(dates||[]).filter(Boolean).join(",");
  if(!dl){R();return}
  api("/api/weather?dates="+dl).then(function(w){
    if(w && w.forecasts){for(var k in w.forecasts) P.weather[k]=w.forecasts[k]}
    R();
  });
}
function fetchNow(){
  P.loading=true;R();
  api("/slots?min_score=0&limit=500&date="+today()).then(function(d){
    var all=(d&&d.slots)?d.slots:[];var cur=nowTime();
    P.nowSlots=all.filter(function(s){return s.time && s.time>=cur})
                  .sort(function(a,b){return(a.time||"").localeCompare(b.time||"")});
    P.loading=false;
    loadWeather([today()]);
  });
}
function fetchCourseSlots(){
  if(!P.coursePick){fetchNow();return}
  P.loading=true;P.courseWeek=null;R();
  var url="/api/course/"+encodeURIComponent(P.coursePick)+"/week?days="+P.courseWeekDays;
  api(url).then(function(d){
    if(!d || !d.days){
      P.courseWeek={course_id:P.coursePick,days:[],total_slots:0,error:(d&&d.detail)||"Couldn't load tee times"};
      P.loading=false;R();return;
    }
    P.courseWeek=d;P.loading=false;
    loadWeather(d.days.map(function(x){return x.date}));
  });
}
function fetchAll(){
  P.loading=true;R();
  var url="/slots?min_score=0&limit=500";
  if(P.course) url+="&course_id="+P.course;
  api(url).then(function(d){
    P.slots=(d&&d.slots)?d.slots:[];P.loading=false;
    var dates={};P.slots.forEach(function(s){if(s.date)dates[s.date]=1});
    loadWeather(Object.keys(dates).slice(0,7));
  });
}
function fetchSearch(){
  P.loading=true;P.searchLimit=30;R();
  var url="/slots?min_score=0&limit=500";
  if(P.searchCourse) url+="&course_id="+P.searchCourse;
  if(P.date) url+="&date="+P.date;
  api(url).then(function(d){
    P.searchSlots=(d&&d.slots)?d.slots:[];P.loading=false;
    var dates={};P.searchSlots.forEach(function(s){if(s.date)dates[s.date]=1});
    loadWeather(Object.keys(dates).slice(0,7));
  });
}
function fetchWebAlerts(){
  if(!P.sessionId)return;
  api("/api/web-alerts/"+P.sessionId).then(function(d){P.webAlerts=(d&&d.alerts)?d.alerts:[];R()});
}
function checkWebAlerts(){
  if(!P.sessionId)return;
  api("/api/web-alerts/check/"+P.sessionId).then(function(d){
    if(d && d.matches && d.matches.length>0){
      P.webMatches=P.webMatches.concat(d.matches);R();
      if("Notification" in window && Notification.permission==="granted"){
        d.matches.forEach(function(m){m.slots.forEach(function(s){
          new Notification("Tee Time Alert: "+m.course_name,{
            body:fd(s.date)+" at "+ft(s.time)+" — $"+Math.round(s.price||0)
          });
        })});
      }
    }
  }).catch(function(){});
}
function fetchSnipes(){
  if(!P.ct)return;
  api("/api/snipes/"+P.ct).then(function(d){P.snipes=(d&&d.snipes)?d.snipes:[];R()});
}

/* ==========================================================================
   Actions
   ========================================================================== */
function triggerScan(){
  if(P.scanning)return;
  P.scanning=true;R();
  api("/scan/trigger",{method:"POST"});
  setTimeout(function(){
    P.scanning=false;
    if(P.tab==="wknd") fetchAll();
    else if(P.tab==="now"){ if(P.coursePick) fetchCourseSlots(); else fetchNow() }
    else if(P.tab==="search") fetchSearch();
  },6000);
}
function setTab(t){
  P.tab=t;P.cmsg=null;P.sm=null;P.alertMsg=null;R();
  if(t==="now"){ if(P.coursePick) fetchCourseSlots(); else fetchNow(); }
  else if(t==="wknd") fetchAll();
  else if(t==="search"){ P.date=P.date||nsat(); P.searchLimit=30; fetchSearch(); }
  else if(t==="alerts"){ fetchWebAlerts(); checkWebAlerts(); }
  else if(t==="snipe" && P.ct) fetchSnipes();
}
function pickCourse(v){
  P.coursePick=v;
  if(v) localStorage.setItem("tbot_course",v);
  else localStorage.removeItem("tbot_course");
  if(v) fetchCourseSlots(); else fetchNow();
}
function doWebAlert(){
  if(!P.alertCourse){P.alertMsg="error:Please select a course";R();return}
  if(!P.alertEmail || P.alertEmail.indexOf("@")<0){P.alertMsg="error:Please enter a valid email address";R();return}
  var body={
    session_id:P.sessionId,course_id:P.alertCourse,email:P.alertEmail,
    earliest_time:P.alertTimeMin,latest_time:P.alertTimeMax,
    date_from:P.alertDateFrom||null,date_to:P.alertDateTo||null,
    min_players:P.alertPlayers
  };
  api("/api/web-alerts",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(body)}).then(function(d){
    if(d && d.id){
      P.alertMsg="ok:Alert set for "+d.course;
      fetchWebAlerts();
      if("Notification" in window && Notification.permission==="default") Notification.requestPermission();
    } else {
      P.alertMsg="error:"+(d && d.detail?d.detail:"Couldn't create alert");
    }
    R();
  });
}
function deleteWebAlert(id){
  api("/api/web-alerts/"+id+"?session_id="+P.sessionId,{method:"DELETE"}).then(function(){fetchWebAlerts()});
}
function doSnipe(){
  if(!P.ct){P.sm="error:Connect your Telegram first (Account tab)";R();return}
  var body={telegram_chat_id:P.ct,course_id:P.sc,play_day:P.sd,preferred_time:P.st,players:P.sp};
  api("/api/snipe",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(body)}).then(function(d){
    if(d && d.course){
      P.sm="ok:Snipe set for "+d.course+" on "+d.play_date+" — opens "+d.release_date+" at midnight";
      fetchSnipes();
    } else {
      P.sm="error:"+(d && d.detail?d.detail:"Couldn't set snipe");
    }
    R();
  });
}
function saveConnected(uid,tok){
  localStorage.setItem("tbot_tid",P.ct);
  localStorage.setItem("tbot_name",P.cn);
  if(tok) localStorage.setItem("tbot_tok",tok);
  P.cmsg="ok:Connected — you'll now get alerts on Telegram. User ID: "+uid;
  R();
}
function doConnect(){
  if(!P.cn || !P.ct){P.cmsg="error:Enter your name and Telegram chat ID";R();return}
  var body={name:P.cn,telegram_chat_id:P.ct,email:P.ce};
  api("/api/connect",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(body)}).then(function(d){
    if(d && d.api_token){saveConnected(d.user_id,d.api_token);return}
    if(d && d.verification_required){
      var code=window.prompt("Check Telegram for a 6-digit verification code:");
      if(!code){P.cmsg="error:Verification cancelled";R();return}
      api("/api/verify-connect",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({telegram_chat_id:P.ct,code:code.trim()})}).then(function(v){
        if(v && v.api_token) saveConnected(v.user_id,v.api_token);
        else { P.cmsg="error:"+(v && v.detail?v.detail:"Verification failed"); R(); }
      });
      return;
    }
    P.cmsg="error:"+(d && d.detail?d.detail:"Couldn't connect");R();
  });
}

/* ==========================================================================
   Shared render helpers
   ========================================================================== */
function courseOptions(sel){
  var h="";
  sorted.forEach(function(e){
    h+='<option value="'+e[0]+'"'+(sel===e[0]?" selected":"")+'>'+escapeHtml(e[1].n)+'</option>';
  });
  return h;
}
function filterSlots(slots){
  return slots.filter(function(s){
    if(P.players && s.players_available && s.players_available<P.players) return false;
    if(s.time && s.time<P.timeMin) return false;
    if(s.time && s.time>P.timeMax) return false;
    return true;
  });
}
function slotCard(s){
  var c=C[s.course_id]||{n:s.course_id,t:""};
  var tier=c.t?' <span class="tier '+tcCls(c.t)+'">'+c.t+'</span>':"";
  var band=priceBand(s.price,s.course_id);
  var priceClass=band==="hot"?"hot":band==="good"?"good":band==="prem"?"prem":"";
  var priceHtml=(s.price>0)?'<span class="slot-price '+priceClass+'">$'+Math.round(s.price)+'</span>'+priceTag(s.price,s.course_id):"";
  var playersHtml='<span>'+(s.players_available||"?")+'p</span>';
  var dateHtml='<span>'+fd(s.date)+'</span>';
  var action=s.booking_url?'<a class="slot-action" href="'+escapeHtml(s.booking_url)+'" target="_blank" rel="noopener">Book</a>':"";
  return '<div class="card"><div class="slot">' +
           '<div class="slot-time">'+ft(s.time)+'</div>' +
           '<div class="slot-info">' +
             '<div class="slot-course">'+escapeHtml(c.n)+tier+'</div>' +
             '<div class="slot-meta">'+dateHtml+priceHtml+playersHtml+'</div>' +
           '</div>' +
           action +
         '</div></div>';
}
function skeletonBlock(n){var h="";for(var i=0;i<(n||4);i++)h+='<div class="skeleton"></div>';return h}
function weatherBadge(d){
  var w=P.weather[d];if(!w)return"";
  var bad=w.is_bad_weather;
  var icon="☀️";
  if(w.conditions){
    var co=w.conditions.join(" ").toLowerCase();
    if(co.indexOf("thunder")>=0) icon="⛈️";
    else if(co.indexOf("rain")>=0||co.indexOf("drizzle")>=0) icon="🌧️";
    else if(co.indexOf("snow")>=0) icon="🌨️";
    else if(co.indexOf("cloud")>=0) icon="⛅";
    else icon="🌤️";
  }
  var extra="";
  if(w.rain_chance>0) extra+=" · "+w.rain_chance+"%";
  if(w.max_wind_mph>10) extra+=" · "+w.max_wind_mph+"mph";
  return '<span class="day-weather'+(bad?" bad":"")+'">'+icon+' '+w.avg_temp_f+'°F'+extra+'</span>';
}
function weatherWarning(d){
  var w=P.weather[d];if(!w||!w.is_bad_weather)return"";
  return '<div class="banner err"><span class="banner-icon">⚠️</span><span class="banner-body">'+escapeHtml(w.summary)+' — consider another day</span></div>';
}
function banner(kind,icon,body){
  return '<div class="banner '+kind+'"><span class="banner-icon">'+icon+'</span><span class="banner-body">'+body+'</span></div>';
}
function dayHeader(date,count){
  return '<div class="day-header">' +
           '<div class="day-title"><span class="day-date">'+fd(date)+'</span>' +
           '<span class="day-count">'+count+' time'+(count!==1?"s":"")+'</span></div>' +
           weatherBadge(date) +
         '</div>';
}
function segmentedPlayers(){
  var h='<div class="segmented">';
  [1,2,3,4].forEach(function(n){
    h+='<button class="'+(P.players===n?"active":"")+'" onclick="P.players='+n+';R()">'+n+(n===4?"":"p")+'</button>';
  });
  return h+'</div>';
}
function timeOptions(sel,endAt){
  var end=endAt||"19:00";
  var times=[];
  for(var h=5;h<=18;h++){for(var m=0;m<60;m+=15){
    var t=String(h).padStart(2,"0")+":"+String(m).padStart(2,"0");
    if(t>end) break;
    times.push(t);
  }}
  var out="";
  times.forEach(function(t){out+='<option value="'+t+'"'+(sel===t?" selected":"")+'>'+ft(t)+'</option>'});
  return out;
}
function emptyState(icon,title,hint){
  return '<div class="empty"><div class="empty-icon">'+icon+'</div>'+
    '<div class="empty-title">'+title+'</div>'+
    '<div class="empty-hint">'+hint+'</div></div>';
}
function messageBanner(msg){
  if(!msg)return "";
  var parts=msg.split(":");
  var type=parts.shift();var body=escapeHtml(parts.join(":"));
  var kind=type==="ok"?"info":"err";
  var icon=type==="ok"?"✓":"✕";
  return '<div class="banner '+kind+'"><span class="banner-icon">'+icon+'</span><span class="banner-body">'+body+'</span></div>';
}

/* ==========================================================================
   Views
   ========================================================================== */
function rNow(){
  var h='<div class="section-head"><div class="section-title">Tee times</div>' +
        '<div class="section-sub">Pick a course to see every open time for the next 7 days.</div></div>';
  h+='<div class="field"><select class="select" onchange="pickCourse(this.value)">' +
       '<option value=""'+(P.coursePick===""?" selected":"")+'>Today only — all courses</option>' +
       courseOptions(P.coursePick) + '</select></div>';

  if(P.loading) return h+skeletonBlock(5);

  if(P.coursePick){
    var w=P.courseWeek;
    if(!w) return h+skeletonBlock(5);
    if(w.error) return h+emptyState("⚠️","Couldn't load this course",escapeHtml(w.error));
    var total=w.total_slots||0;
    var nDays=(w.days&&w.days.length)||P.courseWeekDays;

    // Surface persistent course-level scan problems as a prominent banner so
    // users don't mistake scanner failure for genuine lack of availability.
    if(w.course_scan_state==="unsupported"){
      h+=banner("warn","🔧","<b>This course isn't scanned yet</b><div style=\"margin-top:4px;color:var(--text-2)\">"+
        "Our scanner doesn't support <b>"+escapeHtml(w.course_platform||"this provider")+"</b> yet. "+
        "Availability below reflects only cached data. Use the course's booking link for now.</div>");
    } else if(w.course_scan_state==="error"){
      h+=banner("err","⚠️","<b>Scanner is failing for this course</b><div style=\"margin-top:4px;color:var(--text-2)\">"+
        "We couldn't reach <b>"+escapeHtml(w.course_platform||"the provider")+"</b> on any of the last 7 scan attempts. "+
        "What's shown below may be stale or incomplete.</div>");
    }

    h+='<div style="font-size:12.5px;color:var(--text-2);margin-bottom:4px">' +
       escapeHtml(w.course_name||P.coursePick) + ' · ' + total + ' open time' + (total!==1?"s":"") +
       ' across the next ' + nDays + ' days</div>';
    (w.days||[]).forEach(function(day){
      var ds=day.slots||[];
      h+=dayHeader(day.date,ds.length);
      h+=weatherWarning(day.date);
      if(ds.length){
        ds.forEach(function(s){h+=slotCard(s)});
        return;
      }
      // No slots — explain WHY based on the latest scan attempt for this day
      // instead of the previous generic "no tee times on this day yet" that
      // couldn't distinguish "empty" from "scanner broken".
      var st=day.scan_status||"never_scanned";
      var msg;
      if(st==="ok"||st==="empty"||st==="stale_ok"){
        msg="No tee times available for this day.";
      } else if(st==="unsupported"){
        msg="Our scanner doesn't support "+escapeHtml(w.course_platform||"this provider")+" yet — check the course's booking page directly.";
      } else if(st==="config_missing"){
        msg="Scan is misconfigured for this course (missing provider ID). Reported to the team.";
      } else if(st==="error"){
        msg="Scanner failed for this day. We'll retry on the next cycle.";
      } else if(st==="skipped"){
        msg="Scan skipped this day (bad weather forecast).";
      } else if(st==="never_scanned"){
        msg="Not scanned yet — the next scan cycle will cover this day.";
      } else {
        msg="No tee times available for this day.";
      }
      h+='<div class="empty-inline">'+msg+'</div>';
    });
    return h;
  }

  // Default: today across all courses
  var td=today();
  h+=dayHeader(td,P.nowSlots.length);
  h+=weatherWarning(td);
  var filtered=P.nowSlots.filter(function(s){
    if(P.players && s.players_available && s.players_available<P.players) return false;
    return true;
  });
  if(!filtered.length){
    h+=emptyState("🏌️","No tee times left today","Pick a course above to see the next 7 days, or check the All week tab.");
    return h;
  }
  var showing=filtered.slice(0,P.nowLimit);
  showing.forEach(function(s){h+=slotCard(s)});
  if(filtered.length>P.nowLimit){
    h+='<button class="button secondary full" style="margin-top:10px" onclick="P.nowLimit+=10;R()">Show more ('+(filtered.length-P.nowLimit)+' more)</button>';
  }
  return h;
}

function rWknd(){
  var h='<div class="section-head"><div class="section-title">All week</div>' +
        '<div class="section-sub">Every open time across all '+scanN+' courses, grouped by date.</div></div>';
  h+='<div class="row" style="margin-bottom:12px">' +
       '<select class="select" onchange="P.course=this.value;fetchAll()">' +
         '<option value=""'+(P.course===""?" selected":"")+'>All courses</option>' +
         courseOptions(P.course) +
       '</select></div>';
  h+='<div class="row" style="margin-bottom:12px"><div style="flex:2">' +
       '<div class="label">Players</div>'+segmentedPlayers()+'</div>' +
     '<div style="flex:1.2"><div class="label">Earliest</div>' +
       '<select class="select" onchange="P.timeMin=this.value;R()">'+timeOptions(P.timeMin)+'</select></div>' +
     '<div style="flex:1.2"><div class="label">Latest</div>' +
       '<select class="select" onchange="P.timeMax=this.value;R()">'+timeOptions(P.timeMax)+'</select></div></div>';

  if(P.loading) return h+skeletonBlock(6);

  var filtered=filterSlots(P.slots);
  if(!filtered.length) return h+emptyState("🔍","No matches","Try widening the time range, lowering player count, or tap the refresh button.");

  var byDate={};
  filtered.forEach(function(s){(byDate[s.date]=byDate[s.date]||[]).push(s)});
  var dates=Object.keys(byDate).sort();
  dates.forEach(function(d){
    var ds=byDate[d];
    h+=dayHeader(d,ds.length);
    h+=weatherWarning(d);
    ds.sort(function(a,b){return(b.score||0)-(a.score||0)});
    ds.slice(0,30).forEach(function(s){h+=slotCard(s)});
    if(ds.length>30) h+='<div class="empty-inline">+ '+(ds.length-30)+' more times</div>';
  });
  h+='<div style="text-align:center;font-size:11px;color:var(--text-3);margin-top:14px">Showing '+filtered.length+' times across '+dates.length+' day'+(dates.length!==1?"s":"")+'</div>';
  return h;
}

function rSearch(){
  var h='<div class="section-head"><div class="section-title">Search</div>' +
        '<div class="section-sub">Filter by course and date.</div></div>';
  h+='<div class="row" style="margin-bottom:12px">' +
       '<select class="select" onchange="P.searchCourse=this.value">' +
         '<option value=""'+(P.searchCourse===""?" selected":"")+'>All courses</option>' +
         courseOptions(P.searchCourse) +
       '</select>' +
       '<input type="date" class="input" style="max-width:160px" value="'+escapeHtml(P.date)+'" onchange="P.date=this.value">' +
     '</div>';
  h+='<div class="row" style="margin-bottom:12px"><div style="flex:2">' +
       '<div class="label">Players</div>'+segmentedPlayers()+'</div>' +
     '<div style="flex:1.2"><div class="label">Earliest</div>' +
       '<select class="select" onchange="P.timeMin=this.value">'+timeOptions(P.timeMin)+'</select></div>' +
     '<div style="flex:1.2"><div class="label">Latest</div>' +
       '<select class="select" onchange="P.timeMax=this.value">'+timeOptions(P.timeMax)+'</select></div></div>';
  h+='<button class="button full" onclick="fetchSearch()">Search</button>';

  if(P.loading) return h+'<div style="margin-top:14px">'+skeletonBlock(4)+'</div>';

  var filtered=filterSlots(P.searchSlots);
  if(!filtered.length && P.searchSlots.length===0) return h;
  if(!filtered.length) return h+emptyState("🔍","No matches","Nothing matches your filters. Try a wider range.");

  var byDate={};filtered.forEach(function(s){(byDate[s.date]=byDate[s.date]||[]).push(s)});
  var dates=Object.keys(byDate).sort();
  var shown=0;
  dates.forEach(function(d){
    if(shown>=P.searchLimit)return;
    var ds=byDate[d];
    h+=dayHeader(d,ds.length);
    h+=weatherWarning(d);
    ds.sort(function(a,b){return(b.score||0)-(a.score||0)});
    ds.forEach(function(s){if(shown<P.searchLimit){h+=slotCard(s);shown++}});
  });
  if(shown<filtered.length){
    h+='<button class="button secondary full" style="margin-top:10px" onclick="P.searchLimit+=30;R()">Show more ('+(filtered.length-shown)+' more)</button>';
  }
  return h;
}

function rAlerts(){
  var h='<div class="section-head"><div class="section-title">Alerts</div>' +
        '<div class="section-sub">Get notified the moment a matching tee time opens up.</div></div>';

  if(P.webMatches.length>0){
    var matchHtml='<b>'+P.webMatches.length+' new match'+(P.webMatches.length!==1?"es":"")+' found</b>';
    h+='<div class="banner warn"><span class="banner-icon">🔔</span><span class="banner-body">'+matchHtml+
       '<div style="margin-top:8px">';
    P.webMatches.forEach(function(m){m.slots.forEach(function(s){h+=slotCard(s)})});
    h+='<button class="button ghost sm" style="margin-top:8px" onclick="P.webMatches=[];R()">Dismiss</button></div></span></div>';
  }

  h+='<div class="section-head" style="margin-top:22px"><div class="section-title" style="font-size:15px">New alert</div></div>';
  h+='<div class="field"><div class="label">Course</div>' +
     '<select class="select" onchange="P.alertCourse=this.value">' +
       '<option value="">Select a course…</option>'+courseOptions(P.alertCourse)+'</select></div>';
  h+='<div class="field"><div class="label">Email for notifications</div>' +
     '<input type="email" class="input" placeholder="you@email.com" value="'+escapeHtml(P.alertEmail)+'" oninput="P.alertEmail=this.value;localStorage.setItem(\'tbot_email\',this.value)"></div>';
  h+='<div class="row"><div><div class="label">Earliest</div>' +
       '<select class="select" onchange="P.alertTimeMin=this.value">'+timeOptions(P.alertTimeMin)+'</select></div>' +
     '<div><div class="label">Latest</div>' +
       '<select class="select" onchange="P.alertTimeMax=this.value">'+timeOptions(P.alertTimeMax)+'</select></div>' +
     '<div><div class="label">Players</div>' +
       '<select class="select" onchange="P.alertPlayers=parseInt(this.value)">';
  [1,2,3,4].forEach(function(n){h+='<option value="'+n+'"'+(P.alertPlayers===n?" selected":"")+'>'+n+'+</option>'});
  h+='</select></div></div>';
  h+='<div class="row" style="margin-top:10px"><div><div class="label">From (optional)</div>' +
       '<input type="date" class="input" value="'+escapeHtml(P.alertDateFrom)+'" onchange="P.alertDateFrom=this.value"></div>' +
     '<div><div class="label">To (optional)</div>' +
       '<input type="date" class="input" value="'+escapeHtml(P.alertDateTo)+'" onchange="P.alertDateTo=this.value"></div></div>';
  h+='<button class="button full" style="margin-top:14px" onclick="doWebAlert()">Set alert</button>';
  h+=messageBanner(P.alertMsg);

  h+='<div class="section-head" style="margin-top:26px"><div class="section-title" style="font-size:15px">Active alerts</div></div>';
  if(P.webAlerts.length===0){
    h+=emptyState("🔕","No active alerts","Create one above — you'll get an email and a browser notification when something matches.");
  } else {
    P.webAlerts.forEach(function(a){
      var cn=a.course_name||a.course_id;
      var range=ft(a.earliest_time)+" – "+ft(a.latest_time);
      var dateRange=a.date_from?fd(a.date_from)+(a.date_to?" → "+fd(a.date_to):""):"";
      h+='<div class="list-row"><div style="min-width:0;flex:1">' +
         '<div class="list-title">'+escapeHtml(cn)+'</div>' +
         '<div class="list-meta">'+range+(a.min_players>1?' · '+a.min_players+"+ players":"")+(dateRange?" · "+dateRange:"")+'</div>' +
         (a.email?'<div class="list-meta" style="color:var(--accent)">'+escapeHtml(a.email)+'</div>':"")+
         '</div>' +
         '<button class="button danger-ghost sm" onclick="deleteWebAlert('+a.id+')">Remove</button></div>';
    });
  }
  h+='<div style="font-size:11.5px;color:var(--text-3);margin-top:18px;line-height:1.6">The scanner checks every ~60s. Matching times trigger an email, a browser notification, and (if connected) a Telegram DM.</div>';
  return h;
}

function rSnipe(){
  var h='<div class="section-head"><div class="section-title">Snipe a tee time</div>' +
        '<div class="section-sub">Get an instant alert at midnight when a course releases a date you want.</div></div>';
  if(!P.ct){
    h+='<div class="empty"><div class="empty-icon">🔗</div>' +
       '<div class="empty-title">Connect Telegram to set a snipe</div>' +
       '<div class="empty-hint">Snipes fire as a Telegram DM within seconds of the release.</div>' +
       '<button class="button" style="margin-top:14px" onclick="setTab(\'connect\')">Go to Account</button></div>';
    return h;
  }
  h+='<div class="field"><div class="label">Course</div>' +
     '<select class="select" onchange="P.sc=this.value">'+courseOptions(P.sc)+'</select></div>';
  h+='<div class="row"><div><div class="label">Day</div>' +
       '<select class="select" onchange="P.sd=this.value">' +
         '<option value="sat"'+(P.sd==="sat"?" selected":"")+'>Saturday</option>' +
         '<option value="sun"'+(P.sd==="sun"?" selected":"")+'>Sunday</option>' +
         '<option value="fri"'+(P.sd==="fri"?" selected":"")+'>Friday</option></select></div>' +
     '<div><div class="label">Preferred time</div>' +
       '<select class="select" onchange="P.st=this.value">'+timeOptions(P.st)+
         '<option value="any"'+(P.st==="any"?" selected":"")+'>Any</option>' +
       '</select></div>' +
     '<div><div class="label">Players</div>' +
       '<select class="select" onchange="P.sp=parseInt(this.value)">';
  [2,3,4].forEach(function(n){h+='<option value="'+n+'"'+(P.sp===n?" selected":"")+'>'+n+'</option>'});
  h+='</select></div></div>';
  h+='<button class="button full" style="margin-top:14px" onclick="doSnipe()">Set snipe</button>';
  h+=messageBanner(P.sm);

  if(P.snipes.length){
    h+='<div class="section-head" style="margin-top:26px"><div class="section-title" style="font-size:15px">Active snipes</div></div>';
    P.snipes.forEach(function(s){
      var cn=C[s.course_id]?C[s.course_id].n:s.course_id;
      h+='<div class="list-row"><div><div class="list-title">'+escapeHtml(cn)+'</div>' +
         '<div class="list-meta">'+fd(s.play_date)+' at '+ft(s.preferred_time)+'</div></div>' +
         '<div class="list-meta">Opens '+fd(s.release_date)+'</div></div>';
    });
  }
  h+='<div style="margin-top:22px;padding:14px;background:var(--surface);border:1px solid var(--border);border-radius:var(--radius-sm);font-size:12.5px;color:var(--text-2);line-height:1.6">' +
     '<div style="color:var(--text);font-weight:500;margin-bottom:6px">How releases work</div>' +
     'Each course opens tee times a fixed number of days before play — usually at midnight. When you set a snipe, the bot watches the release window every 30 seconds and pings you the instant times go live.</div>';
  h+='<div style="margin-top:12px;padding:14px;background:var(--surface);border:1px solid var(--border);border-radius:var(--radius-sm);font-size:12.5px;color:var(--text-2);line-height:1.6">' +
     '<div style="color:var(--text);font-weight:500;margin-bottom:6px">Telegram shortcut</div>' +
     'You can also set snipes from Telegram: <span class="kbd">SNIPE bolingbrook sat 7am</span></div>';
  return h;
}

function platformColor(s){
  return {golfnow:"#6ee7a0",chronogolf:"#fbbf24",foreup:"#60a5fa",ezlinks:"#c084fc",teeitup:"#f472b6",whoosh:"#34d399",proshop:"#fcd34d",cps_golf:"#22d3ee",golfback:"#a5b4fc"}[s]||"#94a3b8";
}
function rCourses(){
  var h='<div class="section-head"><div class="section-title">Courses</div>' +
        '<div class="section-sub">'+scanN+' courses actively scanning across '+new Set(sorted.map(function(e){return e[1].s})).size+' booking platforms.</div></div>';
  sorted.forEach(function(e){
    var id=e[0],c=e[1];
    var tier=c.t?' <span class="tier '+tcCls(c.t)+'">'+c.t+'</span>':"";
    h+='<div class="course-row" onclick="pickCourse(\''+id+'\');setTab(\'now\')">' +
       '<div style="min-width:0;flex:1"><div class="course-name">'+escapeHtml(c.n)+tier+'</div>' +
       '<div class="course-meta">'+c.d+' mi · '+c.adv+'-day advance'+(c.avg?' · ~$'+c.avg:"")+'</div></div>' +
       '<span class="platform-chip" style="color:'+platformColor(c.s)+'">'+escapeHtml(c.s||"direct")+'</span></div>';
  });
  return h;
}

function rConnect(){
  var h='<div class="section-head"><div class="section-title">Account</div>' +
        '<div class="section-sub">Connect Telegram to get alerts, set snipes, and book faster.</div></div>';
  if(P.ct && localStorage.getItem("tbot_tid")){
    h+='<div class="banner info"><span class="banner-icon">✓</span><span class="banner-body">Connected as <b>'+escapeHtml(localStorage.getItem("tbot_name")||P.ct)+'</b> · Chat ID '+escapeHtml(P.ct)+'</span></div>';
    h+='<div class="section-head" style="margin-top:22px"><div class="section-title" style="font-size:15px">Next steps</div></div>';
    h+='<div class="step"><div class="step-num">1</div><div class="step-body">' +
       '<div class="step-title">Send <span class="kbd">HELP</span> to the bot</div>' +
       '<div class="step-hint">See every command you can use.</div></div></div>';
    h+='<div class="step"><div class="step-num">2</div><div class="step-body">' +
       '<div class="step-title">Try a snipe</div>' +
       '<div class="step-hint">Tap Snipe, pick a course and date, and I\'ll ping you the moment it releases.</div></div></div>';
    h+='<button class="button ghost full" style="margin-top:14px" onclick="if(confirm(\'Sign out of this device?\')){localStorage.removeItem(\'tbot_tid\');localStorage.removeItem(\'tbot_name\');localStorage.removeItem(\'tbot_tok\');P.ct=\'\';P.cn=\'\';R()}">Sign out</button>';
    return h;
  }
  h+='<div class="step"><div class="step-num">1</div><div class="step-body">' +
     '<div class="step-title">Open the bot in Telegram</div>' +
     '<div class="step-hint"><a class="link" href="https://t.me/chi_teetime_bot" target="_blank" rel="noopener">@chi_teetime_bot</a> — send <span class="kbd">/start</span> and the bot will reply with your chat ID.</div></div></div>';
  h+='<div class="step"><div class="step-num">2</div><div class="step-body">' +
     '<div class="step-title">Enter your details</div>' +
     '<div class="field" style="margin-top:10px"><div class="label">Your name</div>' +
       '<input class="input" placeholder="e.g. John Smith" value="'+escapeHtml(P.cn)+'" oninput="P.cn=this.value"></div>' +
     '<div class="field"><div class="label">Telegram chat ID</div>' +
       '<input class="input" placeholder="e.g. 698266341" value="'+escapeHtml(P.ct)+'" oninput="P.ct=this.value"></div>' +
     '<div class="field"><div class="label">Email (optional)</div>' +
       '<input class="input" placeholder="you@email.com" value="'+escapeHtml(P.ce)+'" oninput="P.ce=this.value"></div>' +
     '</div></div>';
  h+='<div class="step"><div class="step-num">3</div><div class="step-body">' +
     '<div class="step-title">Connect</div>' +
     '<button class="button full" style="margin-top:10px" onclick="doConnect()">Connect to the bot</button>' +
     '</div></div>';
  h+=messageBanner(P.cmsg);
  return h;
}

/* ==========================================================================
   Shell (header + tabs)
   ========================================================================== */
var TABS = [
  {k:"now",    label:"Tee times"},
  {k:"wknd",   label:"All week"},
  {k:"search", label:"Search"},
  {k:"alerts", label:"Alerts"},
  {k:"snipe",  label:"Snipe"},
  {k:"courses",label:"Courses"},
  {k:"connect",label:"Account"}
];
function R(){
  var live=P.health && P.health.status==="ok";
  var connected=!!(P.ct && localStorage.getItem("tbot_tid"));

  var h='<div class="header">';
  h+='<div class="brand">' +
       '<div class="brand-mark">⛳</div>' +
       '<div class="brand-text"><h1>Tee Time Bot</h1>' +
       '<div class="brand-sub"><span class="live-dot '+(live?"":"offline")+'"></span>' +
       (live?"Live":"Connecting")+' · '+scanN+' courses'+(connected?' · signed in':"")+'</div></div></div>';
  h+='<button class="icon-btn'+(P.scanning?" loading":"")+'" onclick="triggerScan()" '+(P.scanning?"disabled":"")+' title="Trigger a fresh scan">' +
     '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">' +
     '<path d="M21 12a9 9 0 11-3-6.7"/><path d="M21 4v5h-5"/></svg></button>';
  h+='</div>';

  h+='<div class="tabs" role="tablist">';
  for(var i=0;i<TABS.length;i++){
    var t=TABS[i];var badge="";
    if(t.k==="alerts" && P.webMatches.length>0) badge=' <span class="tab-badge">'+P.webMatches.length+'</span>';
    h+='<button class="tab'+(P.tab===t.k?" active":"")+'" onclick="setTab(\''+t.k+'\')">'+t.label+badge+'</button>';
  }
  h+='</div>';

  h+='<div class="content">';
  if(P.tab==="now")         h+=rNow();
  else if(P.tab==="wknd")   h+=rWknd();
  else if(P.tab==="search") h+=rSearch();
  else if(P.tab==="alerts") h+=rAlerts();
  else if(P.tab==="snipe")  h+=rSnipe();
  else if(P.tab==="courses")h+=rCourses();
  else if(P.tab==="connect")h+=rConnect();
  h+='</div>';

  h+='<div class="footer">Auto-refreshes every 60 seconds · Chicago tee times</div>';

  document.getElementById("app").innerHTML=h;
}

/* ==========================================================================
   Bootstrap
   ========================================================================== */
var savedTid=localStorage.getItem("tbot_tid");
var savedName=localStorage.getItem("tbot_name");
if(savedTid) P.ct=savedTid;
if(savedName) P.cn=savedName;
var savedCourse=localStorage.getItem("tbot_course");
if(savedCourse && C[savedCourse]) P.coursePick=savedCourse;
var savedEmail=localStorage.getItem("tbot_email");
if(savedEmail) P.alertEmail=savedEmail;
var sid=localStorage.getItem("tbot_sid");
if(!sid){
  sid=crypto.randomUUID?crypto.randomUUID():"s-"+Date.now()+"-"+Math.random().toString(36).substr(2,9);
  localStorage.setItem("tbot_sid",sid);
}
P.sessionId=sid;

api("/health").then(function(d){P.health=d;R()});
R();
if(P.coursePick) fetchCourseSlots(); else fetchNow();

setInterval(function(){
  if(P.tab==="wknd") fetchAll();
  else if(P.tab==="now"){ if(P.coursePick) fetchCourseSlots(); else fetchNow() }
  if(P.sessionId) checkWebAlerts();
},60000);
</script>
</body>
</html>"""
