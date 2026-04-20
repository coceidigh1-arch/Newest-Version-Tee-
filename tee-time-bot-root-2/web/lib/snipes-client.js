"use client";
// Client-side fetchers for /api/snipes and /api/snipe. Proxies through the
// /backend/* rewrite, same as alerts-client.

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

export async function listSnipes(chatId) {
  if (!chatId) return [];
  const d = await http(`/api/snipes/${encodeURIComponent(chatId)}`);
  return d?.snipes || [];
}

export async function createSnipe(chatId, body) {
  return http(`/api/snipe`, {
    method: "POST",
    body: JSON.stringify({ telegram_chat_id: chatId, ...body }),
  });
}
