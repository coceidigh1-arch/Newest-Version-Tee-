// Server-side fetcher for the tee-time-bot FastAPI backend.
// Pulls /slots + /courses and shapes them into the Fairway frontend's data model.
//
// Falls back to the sample data in ./data.js when BACKEND_URL is unset or the
// backend is unreachable — the mockup screens keep working offline.

import {
  COURSES as SAMPLE_COURSES,
  TEE_TIMES as SAMPLE_TEE_TIMES,
  ALERTS as SAMPLE_ALERTS,
  SNIPES as SAMPLE_SNIPES,
} from "./data.js";

const BACKEND_URL = process.env.BACKEND_URL || process.env.NEXT_PUBLIC_BACKEND_URL || "";

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

function dayFromISODate(iso) {
  const d = new Date(`${iso}T00:00:00`);
  return DAY_NAMES[d.getUTCDay()] || "";
}

function pickWx(slot) {
  // Derive a weather glyph from slot.temp/wind if the backend ever attaches them.
  // For now use sun as a default.
  if (slot.temp != null && slot.temp < 50) return "cloud";
  if (slot.wind != null && slot.wind > 12) return "wind";
  return "sun";
}

function sunriseForDate(/* iso */) {
  return "06:12";
}

// Heuristic score (0-100) when backend score is 0 (unseeded).
function heuristicScore(slot, course) {
  let score = 0;
  // Tier
  const tier = course?.tier || "B";
  score += tier === "A+" ? 28 : tier === "A" ? 20 : tier === "A-" ? 15 : 10;
  // Day: weekends get bonus
  const day = dayFromISODate(slot.date);
  score += day === "SAT" || day === "SUN" ? 18 : day === "FRI" ? 10 : 5;
  // Time: early morning = prime
  const [h, m] = (slot.time || "00:00").split(":").map(Number);
  const mins = h * 60 + (m || 0);
  if (mins >= 330 && mins <= 480) score += 18;       // 5:30–8:00
  else if (mins >= 300 && mins <= 600) score += 10;  // 5:00–10:00
  else score += 3;
  // Price: lower = better
  const p = Number(slot.price || 0);
  if (p === 0) score += 10;
  else if (p <= 80) score += 15;
  else if (p <= 120) score += 10;
  else if (p <= 160) score += 6;
  else score += 2;
  // Players
  const avail = Number(slot.players_available || 4);
  score += avail >= 4 ? 8 : avail >= 2 ? 5 : 2;
  return Math.min(100, Math.max(0, score));
}

function deriveSignals(slot, course, score) {
  const out = [];
  if (score >= 90) out.push("prime");
  else if (score >= 82 && course?.tier === "A+") out.push("prime");
  const p = Number(slot.price || 0);
  if (p > 0 && p <= 75) out.push("deal");
  if ((slot.players_available || 0) === 4 && course?.tier === "A+") out.push("rare");
  return out;
}

function deriveReason(slot, course, score) {
  const bits = [];
  if (course?.tier === "A+") bits.push("A+ course");
  const p = Number(slot.price || 0);
  if (p > 0 && p <= 75) bits.push(`$${p} — under typical`);
  const [h] = (slot.time || "06:00").split(":").map(Number);
  if (h <= 7) bits.push("prime early window");
  if (!bits.length) bits.push(`Score ${score}/100`);
  return bits.join(" · ");
}

function transformCourse(c, i) {
  return {
    id: c.id,
    name: c.name,
    short: c.tier ? `${c.tier} · ${c.platform}` : c.platform,
    tier: c.tier || "B",
    city: c.city || "Chicago area",
    distance: c.distance_miles ?? 0,
    dir: c.direction || "",
    platform: (c.platform || "").replace(/^./, (ch) => ch.toUpperCase()),
  };
}

function transformSlot(slot, courseById, rank) {
  const course = courseById[slot.course_id];
  const backendScore = Number(slot.score || 0);
  const score = backendScore > 0 ? backendScore : heuristicScore(slot, course);
  return {
    id: slot.id,
    course: slot.course_id,
    date: slot.date,
    day: dayFromISODate(slot.date),
    time: slot.time,
    price: Math.round(Number(slot.price || 0)),
    players: slot.players_available ?? 4,
    slotsLeft: slot.players_available ?? 4,
    score,
    rank,
    signals: deriveSignals(slot, course, score),
    wx: pickWx(slot),
    temp: slot.temp ?? 58,
    wind: slot.wind ?? 6,
    sunrise: sunriseForDate(slot.date),
    reason: deriveReason(slot, course, score),
    booking_url: slot.booking_url,
    source: slot.source,
    action: slot.action,
  };
}

export async function getCourses() {
  const data = await fetchJson("/courses");
  const raw = Array.isArray(data?.courses) ? data.courses : null;
  if (!raw || !raw.length) return SAMPLE_COURSES;
  return raw.map(transformCourse);
}

export async function getTeeTimes({ limit = 30 } = {}) {
  const [coursesData, slotsData] = await Promise.all([
    fetchJson("/courses"),
    fetchJson(`/slots?limit=${limit * 3}`),
  ]);
  const coursesRaw = Array.isArray(coursesData?.courses) ? coursesData.courses : [];
  const slotsRaw = Array.isArray(slotsData?.slots) ? slotsData.slots : [];
  if (!slotsRaw.length) return { teeTimes: SAMPLE_TEE_TIMES, isSample: true };

  const courses = coursesRaw.map(transformCourse);
  const courseById = Object.fromEntries(courses.map((c) => [c.id, c]));

  const shaped = slotsRaw
    .map((s, i) => transformSlot(s, courseById, i + 1))
    .filter((s) => courseById[s.course])
    .sort((a, b) => b.score - a.score || a.date.localeCompare(b.date) || a.time.localeCompare(b.time))
    .slice(0, limit)
    .map((s, i) => ({ ...s, rank: i + 1 }));

  return { teeTimes: shaped, isSample: false };
}

export async function getDashboardData() {
  const [{ teeTimes, isSample }, courses] = await Promise.all([
    getTeeTimes({ limit: 12 }),
    getCourses(),
  ]);
  return { teeTimes, courses, isSample };
}

export { SAMPLE_ALERTS as ALERTS, SAMPLE_SNIPES as SNIPES };
