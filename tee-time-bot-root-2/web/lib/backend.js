// Server-side fetcher for the tee-time-bot FastAPI backend.
// Pulls /slots + /courses + /api/weather, scores each slot with the real
// scoring rules (ported in ./scoring.js), derives alerts from slots that
// have been ALERTed/CONFIRMed/AUTOBOOKed, and shapes everything into the
// Fairway frontend model.
//
// Falls back to sample data when BACKEND_URL is unset or the backend is
// unreachable — the mockup keeps rendering offline.

import {
  COURSES as SAMPLE_COURSES,
  TEE_TIMES as SAMPLE_TEE_TIMES,
  ALERTS as SAMPLE_ALERTS,
  SNIPES as SAMPLE_SNIPES,
} from "./data.js";
import { DEFAULT_PREFS, scoreTeeTime } from "./scoring.js";

const BACKEND_URL =
  process.env.BACKEND_URL || process.env.NEXT_PUBLIC_BACKEND_URL || "";

async function fetchJson(path, { revalidate = 60 } = {}) {
  if (!BACKEND_URL) return null;
  try {
    const res = await fetch(`${BACKEND_URL}${path}`, { next: { revalidate } });
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
}

const DAY_NAMES = ["SUN", "MON", "TUE", "WED", "THU", "FRI", "SAT"];
const DAY_LONG = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];
const MONTH_SHORT = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

function dayFromISODate(iso) {
  if (!iso) return "";
  const d = new Date(`${iso}T00:00:00Z`);
  return DAY_NAMES[d.getUTCDay()] || "";
}

function formatHumanDate(iso) {
  if (!iso) return "";
  const d = new Date(`${iso}T00:00:00Z`);
  return `${DAY_LONG[d.getUTCDay()]} ${MONTH_SHORT[d.getUTCMonth()]} ${d.getUTCDate()}`;
}

// Condition string → Fairway wx glyph (backend emits e.g. "Clear", "Clouds",
// "Rain", "Drizzle", "Thunderstorm", "Snow").
function conditionToGlyph(conditions, wind) {
  const first = (conditions?.[0] || "").toLowerCase();
  if (first.includes("clear") || first === "") return "sun";
  if (first.includes("rain") || first.includes("drizzle") || first.includes("snow") || first.includes("storm")) {
    return "drizzle";
  }
  if (first.includes("cloud") || first.includes("fog") || first.includes("mist")) return "cloud";
  if (wind != null && wind >= 18) return "wind";
  return "sun";
}

function approxSunriseForMonth(iso) {
  // Chicago-ish sunrise approximation. Only used as a fallback when weather
  // doesn't include sunrise data.
  const month = iso ? Number(iso.slice(5, 7)) : 4;
  const table = {
    1: "07:18", 2: "07:02", 3: "06:30", 4: "05:45", 5: "05:20",
    6: "05:15", 7: "05:25", 8: "05:55", 9: "06:25", 10: "07:00",
    11: "06:35", 12: "07:10",
  };
  return table[month] || "06:15";
}

function deriveSignals(slot, course, score) {
  const out = [];
  if (score >= 90) out.push("prime");
  else if (score >= 82 && course?.tier === "A+") out.push("prime");
  const p = Number(slot.price || 0);
  if (p > 0 && p <= 75) out.push("deal");
  if ((slot.players_available || 0) === 4 && course?.tier === "A+" && score >= 80) out.push("rare");
  return out;
}

function deriveReason(slot, course, score, prefs) {
  const bits = [];
  if ((prefs.must_play_courses || []).includes(slot.course_id)) {
    bits.push("Must-play course");
  } else if (course?.tier === "A+") {
    bits.push("A+ tier");
  }
  const p = Number(slot.price || 0);
  const max = Number(prefs.max_price || 150);
  if (p > 0 && p <= max * 0.7) bits.push(`$${Math.round(p)} — ${Math.round(max - p)} under max`);
  else if (p > 0 && p <= max) bits.push(`$${Math.round(p)} — under budget`);
  const [h] = (slot.time || "06:00").split(":").map(Number);
  if (h <= 7) bits.push("prime early window");
  if (!bits.length) bits.push(`Score ${score}/100`);
  return bits.join(" · ");
}

function transformCourse(c) {
  return {
    id: c.id,
    name: c.name,
    short: c.notes ? c.notes.split(".")[0].slice(0, 60) : `${c.tier || "B"} · ${c.platform}`,
    tier: c.tier || "B",
    city: c.city || "Chicago area",
    distance: c.distance_miles ?? 0,
    dir: c.direction || "",
    platform: (c.platform || "").replace(/^./, (ch) => ch.toUpperCase()),
    risk_tier: c.risk_tier || "medium",
    booking_url: c.booking_url,
    direct_url: c.direct_url,
    autobook_eligible: c.autobook_eligible,
  };
}

function transformSlot(slot, courseById, rank, weatherByDate, prefs) {
  const course = courseById[slot.course_id];
  const score = scoreTeeTime(slot, prefs, course || {});
  const wx = weatherByDate?.[slot.date] || {};
  return {
    id: slot.id,
    course: slot.course_id,
    date: slot.date,
    day: dayFromISODate(slot.date),
    humanDate: formatHumanDate(slot.date),
    time: slot.time,
    price: Math.round(Number(slot.price || 0)),
    players: slot.players_available ?? 4,
    slotsLeft: slot.players_available ?? 4,
    score,
    rank,
    signals: deriveSignals(slot, course, score),
    wx: wx.glyph || "sun",
    temp: wx.temp ?? null,
    wind: wx.wind ?? null,
    precip: wx.precipitation_prob ?? null,
    sunrise: wx.sunrise || approxSunriseForMonth(slot.date),
    reason: deriveReason(slot, course, score, prefs),
    booking_url: slot.booking_url,
    source: slot.source,
    action: slot.action,
    alerted_at: slot.alerted_at,
    booked_at: slot.booked_at,
    first_seen_at: slot.first_seen_at,
  };
}

async function fetchWeatherForDates(dates) {
  if (!dates?.length) return {};
  const unique = [...new Set(dates)].filter(Boolean).sort();
  if (!unique.length) return {};
  const data = await fetchJson(
    `/api/weather?dates=${encodeURIComponent(unique.join(","))}`
  );
  const forecasts = data?.forecasts || {};
  const out = {};
  for (const [date, fc] of Object.entries(forecasts)) {
    if (!fc) continue;
    const conditions = Array.isArray(fc.conditions) ? fc.conditions : [];
    out[date] = {
      conditions,
      glyph: conditionToGlyph(conditions, fc.max_wind_mph),
      temp: fc.avg_temp_f ?? null,
      wind: fc.max_wind_mph ?? null,
      precipitation_prob: fc.rain_chance ?? null,
      is_bad_weather: fc.is_bad_weather,
      summary: fc.summary,
      sunrise: null,
    };
  }
  return out;
}

function slotsToAlerts(rawSlots, courseById, scoredMap) {
  const events = [];
  for (const s of rawSlots) {
    if (!s.alerted_at && !s.booked_at) continue;
    const scored = scoredMap[s.id] || {};
    const course = courseById[s.course_id];
    if (!course) continue;
    const ts = s.booked_at || s.alerted_at;
    let kind = "new";
    if (s.booked_at) kind = "snipe";
    else if (scored.signals?.includes("deal")) kind = "deal";
    else if (scored.signals?.includes("rare")) kind = "rare";
    else if (scored.signals?.includes("prime")) kind = "new";

    const title =
      s.booked_at ? "Autobook confirmed"
      : kind === "deal" ? "Price drop"
      : kind === "rare" ? "Rare window opened"
      : "New PRIME match";

    events.push({
      id: `a-${s.id}`,
      kind,
      title,
      course: course.name,
      time: `${scored.humanDate || formatHumanDate(s.date)} · ${s.time}`,
      body: scored.reason || `Score ${scored.score || 0}/100`,
      age: ageFromTimestamp(ts),
      ageTs: ts,
      state: s.booked_at ? "success" : undefined,
    });
  }
  events.sort((a, b) => (b.ageTs || "").localeCompare(a.ageTs || ""));
  return events.slice(0, 25);
}

function ageFromTimestamp(ts) {
  if (!ts) return "";
  const d = new Date(ts.replace(" ", "T") + "Z");
  const mins = Math.floor((Date.now() - d.getTime()) / 60000);
  if (mins < 1) return "now";
  if (mins < 60) return `${mins}m`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h`;
  const days = Math.floor(hrs / 24);
  return `${days}d`;
}

export async function getCourses() {
  const data = await fetchJson("/courses");
  const raw = Array.isArray(data?.courses) ? data.courses : null;
  if (!raw?.length) return SAMPLE_COURSES;
  return raw.map(transformCourse);
}

// Returns: { teeTimes, courses, weather, alerts, isSample, openSlotsByCourse }
export async function getDashboardData({ prefs = DEFAULT_PREFS, limit = 20 } = {}) {
  const [coursesData, slotsData] = await Promise.all([
    fetchJson("/courses"),
    fetchJson(`/slots?limit=300`),
  ]);
  const coursesRaw = Array.isArray(coursesData?.courses) ? coursesData.courses : [];
  const slotsRaw = Array.isArray(slotsData?.slots) ? slotsData.slots : [];

  if (!coursesRaw.length || !slotsRaw.length) {
    return {
      teeTimes: SAMPLE_TEE_TIMES,
      courses: SAMPLE_COURSES,
      alerts: SAMPLE_ALERTS,
      openSlotsByCourse: {},
      isSample: true,
    };
  }

  const courses = coursesRaw.map(transformCourse);
  const courseById = Object.fromEntries(courses.map((c) => [c.id, c]));

  // Fetch weather for the dates we actually have slots on.
  const slotDates = [...new Set(slotsRaw.map((s) => s.date))].slice(0, 14);
  const weatherByDate = await fetchWeatherForDates(slotDates);

  // Score + shape every slot, then keep the top `limit`.
  const allScored = slotsRaw
    .map((s) => transformSlot(s, courseById, 0, weatherByDate, prefs))
    .filter((s) => courseById[s.course]);

  const scoredMap = Object.fromEntries(allScored.map((s) => [s.id, s]));

  const teeTimes = [...allScored]
    .sort(
      (a, b) =>
        b.score - a.score ||
        a.date.localeCompare(b.date) ||
        a.time.localeCompare(b.time)
    )
    .slice(0, limit)
    .map((s, i) => ({ ...s, rank: i + 1 }));

  // Open slot count per course (all upcoming, not just top-scored).
  const openSlotsByCourse = {};
  for (const s of allScored) {
    openSlotsByCourse[s.course] = (openSlotsByCourse[s.course] || 0) + 1;
  }

  const alerts = slotsToAlerts(slotsRaw, courseById, scoredMap);

  return {
    teeTimes,
    courses,
    alerts: alerts.length ? alerts : SAMPLE_ALERTS,
    openSlotsByCourse,
    weatherByDate,
    isSample: false,
  };
}

// Kept for backwards-compat with pages that only need tee times.
export async function getTeeTimes({ limit = 20 } = {}) {
  const d = await getDashboardData({ limit });
  return { teeTimes: d.teeTimes, isSample: d.isSample };
}

export { SAMPLE_SNIPES as SNIPES };
