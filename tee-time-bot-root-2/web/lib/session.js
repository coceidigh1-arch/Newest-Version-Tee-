"use client";
// Anonymous browser session. Matches the original dashboard's P.sessionId
// convention — a stable random token stored in localStorage, unused by the
// backend beyond being a key for the user's web alerts.

const KEY = "fairway.session_id";

function rand() {
  if (typeof crypto !== "undefined" && crypto.randomUUID) {
    return crypto.randomUUID().replace(/-/g, "");
  }
  return Math.random().toString(36).slice(2) + Math.random().toString(36).slice(2);
}

export function getSessionId() {
  if (typeof window === "undefined") return "";
  try {
    let id = window.localStorage.getItem(KEY);
    if (!id) {
      id = `fw_${rand()}`.slice(0, 40);
      window.localStorage.setItem(KEY, id);
    }
    return id;
  } catch {
    return "";
  }
}
