// JavaScript port of app/services/scoring.py — scores a slot 0-100 against
// a set of user preferences. Mirrors the Python implementation 1:1 so the
// frontend computes the same numbers the backend would.

export const DEFAULT_PREFS = {
  must_play_courses: [
    "cog_hill_4", "cantigny", "mistwood", "harborside",
    "seven_bridges", "thunderhawk",
  ],
  nice_to_have_courses: ["bolingbrook", "glen_club", "cog_hill_123"],
  preferred_days: ["saturday", "sunday"],
  earliest_time: "05:30",
  latest_time: "08:00",
  max_price: 150,
  players: 2,
  walk_ride: "ride",
  alert_threshold: 55,
  confirm_threshold: 75,
  autobook_threshold: 90,
};

const DAY_NAMES = ["sunday", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday"];

function parseTimeToMinutes(t) {
  if (!t) return NaN;
  const [h, m] = t.split(":").map(Number);
  return h * 60 + (m || 0);
}

export function scoreTeeTime(slot, prefs, course) {
  let score = 0;

  // 1. COURSE PRIORITY (0-30)
  const cid = slot.course_id || slot.course || "";
  if ((prefs.must_play_courses || []).includes(cid)) score += 30;
  else if ((prefs.nice_to_have_courses || []).includes(cid)) score += 20;
  else score += 5;

  // 2. DAY OF WEEK (0-20)
  try {
    const d = new Date(`${slot.date}T00:00:00Z`);
    const dayName = DAY_NAMES[d.getUTCDay()];
    if ((prefs.preferred_days || []).includes(dayName)) score += 20;
    else if (["friday", "thursday"].includes(dayName)) score += 8;
  } catch {}

  // 3. TIME WINDOW (0-20)
  const slotMin = parseTimeToMinutes(slot.time);
  const earliest = parseTimeToMinutes(prefs.earliest_time || "05:00");
  const latest = parseTimeToMinutes(prefs.latest_time || "08:00");
  if (Number.isFinite(slotMin) && Number.isFinite(earliest) && Number.isFinite(latest)) {
    if (slotMin >= earliest && slotMin <= latest) {
      const center = earliest + (latest - earliest) / 2;
      const distance = Math.abs(slotMin - center);
      score += Math.max(20 - Math.floor(distance / 10), 15);
    } else if (slotMin >= earliest && slotMin <= latest + 120) {
      score += 8;
    } else {
      score -= 5;
    }
  } else {
    score += 10;
  }

  // 4. PRICE (0-15)
  const maxPrice = Number(prefs.max_price || 150);
  const price = Number(slot.price || 0);
  if (price <= 0) score += 10;
  else if (price <= maxPrice * 0.7) score += 15;
  else if (price <= maxPrice * 0.85) score += 12;
  else if (price <= maxPrice) score += 8;
  else if (price <= maxPrice * 1.15) score += 3;
  else score -= 5;

  // 5. PLAYER COUNT (0-10)
  const needed = Number(prefs.players || 4);
  const avail = Number(slot.players_available ?? 4);
  if (avail >= needed) score += 10;
  else if (avail >= needed - 1) score += 5;
  else score -= 5;

  // 6. FRESHNESS (0-5)
  if (slot.is_new) score += 5;

  // 7. WALK/RIDE (0-3)
  const prefRide = prefs.walk_ride || "ride";
  const slotRide = slot.walk_ride || "unknown";
  if (prefRide === "either" || slotRide === "unknown" || slotRide === prefRide) score += 3;

  return Math.max(0, Math.min(100, score));
}

export function determineAction(score, course, prefs) {
  const alertT = Number(prefs.alert_threshold || 55);
  const confirmT = Number(prefs.confirm_threshold || 75);
  const autobookT = Number(prefs.autobook_threshold || 90);

  if (score < alertT) return "IGNORE";

  if (score >= autobookT) {
    if (course?.risk_tier === "low" && ["golfnow", "chronogolf"].includes(course.platform)) {
      return "AUTOBOOK";
    }
    if (course?.risk_tier === "medium") return "CONFIRM";
    return "ALERT";
  }

  if (score >= confirmT) {
    if (["custom", "foreup"].includes(course?.platform) || course?.risk_tier === "high") {
      return "ALERT";
    }
    return "CONFIRM";
  }

  return "ALERT";
}
