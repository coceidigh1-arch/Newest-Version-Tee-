"use client";
// Client-side fetchers for the user's saved /api/web-alerts. All calls go
// through the /backend/* rewrite so they're same-origin and pick up the
// user's BACKEND_URL without CORS.

const API = "/backend";

async function http(path, init) {
  const res = await fetch(`${API}${path}`, {
    headers: { "Content-Type": "application/json" },
    cache: "no-store",
    ...init,
  });
  if (!res.ok) {
    let msg = `HTTP ${res.status}`;
    try { const j = await res.json(); msg = j.detail || msg; } catch {}
    throw new Error(msg);
  }
  return res.json();
}

export async function listAlerts(sessionId) {
  if (!sessionId) return [];
  const d = await http(`/api/web-alerts/${sessionId}`);
  return d?.alerts || [];
}

export async function createAlert(sessionId, body) {
  return http(`/api/web-alerts`, {
    method: "POST",
    body: JSON.stringify({ session_id: sessionId, ...body }),
  });
}

export async function deleteAlert(sessionId, alertId) {
  return http(`/api/web-alerts/${alertId}?session_id=${encodeURIComponent(sessionId)}`, {
    method: "DELETE",
  });
}

export async function listCourses() {
  const d = await http(`/courses`);
  return d?.courses || [];
}
