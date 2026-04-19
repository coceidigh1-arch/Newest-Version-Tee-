"use client";
// Stores the user's Telegram chat_id locally. This identifies them to the
// backend's snipe endpoints. The value is the chat_id the user sees in
// conversation with the Telegram bot.

const KEY = "fairway.telegram_chat_id";

export function getChatId() {
  if (typeof window === "undefined") return "";
  try {
    return window.localStorage.getItem(KEY) || "";
  } catch {
    return "";
  }
}

export function setChatId(id) {
  if (typeof window === "undefined") return;
  try {
    if (id) window.localStorage.setItem(KEY, String(id));
    else window.localStorage.removeItem(KEY);
  } catch {}
}
