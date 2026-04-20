// Shared helpers for reading filters from URL search params and writing them
// back — used by both the server page (reads searchParams) and the filters
// client component (builds the next URL).

export function filtersFromSearchParams(sp) {
  if (!sp) return null;
  const get = (k) => {
    const v = typeof sp.get === "function" ? sp.get(k) : sp[k];
    return Array.isArray(v) ? v[0] : v;
  };
  const day = get("day") || null;
  const priceMax = num(get("priceMax"));
  const players = num(get("players"));
  const tMin = num(get("tMin"));
  const tMax = num(get("tMax"));
  const has = day || priceMax != null || players != null || tMin != null || tMax != null;
  if (!has) return null;
  return { day, priceMax, players, tMin, tMax };
}

function num(v) {
  if (v == null || v === "") return null;
  const n = Number(v);
  return Number.isFinite(n) ? n : null;
}

export function buildFilterUrl(base, filters) {
  const qs = new URLSearchParams();
  if (!filters) return base;
  if (filters.day) qs.set("day", filters.day);
  if (filters.priceMax != null) qs.set("priceMax", String(filters.priceMax));
  if (filters.players != null) qs.set("players", String(filters.players));
  if (filters.tMin != null) qs.set("tMin", String(filters.tMin));
  if (filters.tMax != null) qs.set("tMax", String(filters.tMax));
  const s = qs.toString();
  return s ? `${base}?${s}` : base;
}
