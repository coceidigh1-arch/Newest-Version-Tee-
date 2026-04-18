"""
Weather Service

Fetches Chicago forecasts from Open-Meteo (free, no key required) and
falls back to OpenWeather if an API key is configured.

Two entry points:

  get_forecast(date)         -> dict | None  (single-day, used by the scanner)
  get_forecast_batch(dates)  -> dict[date, dict]  (N-day, used by /api/weather)

The batch path makes a single HTTP call covering the whole range, which is
both faster and less fragile than looping per-date (the old code did
N round trips, which was timing out in some Railway paths and returning
an empty {} to the dashboard).

Errors are logged at WARNING level with the specific exception class, so
"weather silently empty" regressions are now visible in Railway logs
rather than hidden behind a swallow-all try/except.
"""

import httpx
import logging
from datetime import datetime

from app.config import settings

logger = logging.getLogger(__name__)

OPENMETEO_URL = "https://api.open-meteo.com/v1/forecast"
OPENWEATHER_URL = "https://api.openweathermap.org/data/2.5/forecast"

_DAILY_FIELDS = (
    "temperature_2m_max,"
    "temperature_2m_min,"
    "precipitation_probability_max,"
    "wind_speed_10m_max,"
    "weather_code"
)


async def get_forecast(date: str) -> dict | None:
    """Single-day forecast. Thin wrapper over get_forecast_batch so both
    entry points share the same implementation and error handling."""
    result = await get_forecast_batch([date])
    return result.get(date)


async def get_forecast_batch(dates: list[str]) -> dict[str, dict]:
    """Fetch forecasts for multiple dates in a single upstream call.
    Returns {date: forecast_dict} for days the upstream returned. Silent
    days (API returned no data for that date) are simply absent from the
    result rather than mapped to None, so callers can `.get(d)` safely."""
    dates = sorted(set(d for d in dates if d))
    if not dates:
        return {}

    # OpenWeather only supports a rolling 5-day window from "now" and uses
    # 3-hour buckets. Skip it unless a key is explicitly configured — for
    # Chicago tee times in the 7-day range, Open-Meteo is simpler and
    # doesn't need a key anyway.
    if settings.OPENWEATHER_API_KEY:
        try:
            ow_result = await _openweather_batch(dates)
            if ow_result:
                return ow_result
        except Exception as exc:
            logger.warning("OpenWeather batch failed (%s: %s) — falling back to Open-Meteo",
                           type(exc).__name__, exc)

    return await _openmeteo_batch(dates)


async def _openmeteo_batch(dates: list[str]) -> dict[str, dict]:
    start_date = dates[0]
    end_date = dates[-1]
    params = {
        "latitude": settings.HOME_LAT,
        "longitude": settings.HOME_LNG,
        "daily": _DAILY_FIELDS,
        "temperature_unit": "fahrenheit",
        "wind_speed_unit": "mph",
        "start_date": start_date,
        "end_date": end_date,
        "timezone": "America/Chicago",
    }

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get(OPENMETEO_URL, params=params)
    except Exception as exc:
        logger.warning("Open-Meteo request failed (%s: %s)", type(exc).__name__, exc)
        return {}

    if response.status_code != 200:
        logger.warning("Open-Meteo returned HTTP %s for %s..%s: %s",
                       response.status_code, start_date, end_date, response.text[:200])
        return {}

    try:
        data = response.json()
    except Exception as exc:
        logger.warning("Open-Meteo response not JSON (%s: %s)", type(exc).__name__, exc)
        return {}

    daily = data.get("daily") or {}
    times = daily.get("time") or []
    if not times:
        logger.warning("Open-Meteo returned no daily.time for %s..%s", start_date, end_date)
        return {}

    out: dict[str, dict] = {}
    for i, d in enumerate(times):
        if d not in dates:
            continue
        temp_max = _safe_index(daily.get("temperature_2m_max"), i)
        temp_min = _safe_index(daily.get("temperature_2m_min"), i)
        rain_pct = _safe_index(daily.get("precipitation_probability_max"), i) or 0
        wind_max = _safe_index(daily.get("wind_speed_10m_max"), i) or 0
        wmo_code = _safe_index(daily.get("weather_code"), i) or 0

        if temp_max is None or temp_min is None:
            continue

        avg_temp = (temp_max + temp_min) / 2
        conditions = _wmo_to_conditions(int(wmo_code))
        is_bad = (
            rain_pct > 60
            or "Thunderstorm" in conditions
            or wind_max > 25
            or avg_temp < 45
        )
        out[d] = {
            "date": d,
            "avg_temp_f": round(avg_temp),
            "rain_chance": int(rain_pct),
            "max_wind_mph": round(wind_max),
            "conditions": conditions,
            "is_bad_weather": is_bad,
            "summary": _summarize(avg_temp, rain_pct / 100, wind_max, conditions),
        }
    return out


async def _openweather_batch(dates: list[str]) -> dict[str, dict]:
    # OpenWeather 5-day / 3-hour endpoint — one call, filter per date.
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get(
                OPENWEATHER_URL,
                params={
                    "lat": settings.HOME_LAT,
                    "lon": settings.HOME_LNG,
                    "appid": settings.OPENWEATHER_API_KEY,
                    "units": "imperial",
                },
            )
    except Exception as exc:
        logger.warning("OpenWeather request failed (%s: %s)", type(exc).__name__, exc)
        return {}

    if response.status_code != 200:
        logger.warning("OpenWeather returned HTTP %s", response.status_code)
        return {}

    data = response.json()
    buckets: dict[str, list] = {}
    for entry in data.get("list", []):
        try:
            entry_dt = datetime.fromtimestamp(entry["dt"])
        except Exception:
            continue
        d = entry_dt.date().isoformat()
        # Focus on morning (6am–noon) — that's when tee times live
        if 6 <= entry_dt.hour <= 12 and d in dates:
            buckets.setdefault(d, []).append(entry)

    out: dict[str, dict] = {}
    for d, entries in buckets.items():
        if not entries:
            continue
        avg_temp = sum(e["main"]["temp"] for e in entries) / len(entries)
        max_rain = max(e.get("pop", 0) for e in entries)
        max_wind = max(e["wind"]["speed"] for e in entries)
        conditions = list({e["weather"][0]["main"] for e in entries})
        is_bad = (
            max_rain > 0.6
            or "Thunderstorm" in conditions
            or max_wind > 25
            or avg_temp < 45
        )
        out[d] = {
            "date": d,
            "avg_temp_f": round(avg_temp),
            "rain_chance": round(max_rain * 100),
            "max_wind_mph": round(max_wind),
            "conditions": conditions,
            "is_bad_weather": is_bad,
            "summary": _summarize(avg_temp, max_rain, max_wind, conditions),
        }
    return out


def _safe_index(seq, i):
    if seq is None:
        return None
    try:
        return seq[i]
    except (IndexError, TypeError):
        return None


def _wmo_to_conditions(code: int) -> list[str]:
    """WMO weather code -> friendly condition tags."""
    if code <= 1:
        return ["Clear"]
    if code <= 3:
        return ["Clouds"]
    if code <= 49:
        return ["Clouds"]
    if code <= 59:
        return ["Drizzle"]
    if code <= 69:
        return ["Rain"]
    if code <= 79:
        return ["Snow"]
    if code <= 84:
        return ["Rain"]
    if code <= 94:
        return ["Rain"]
    if code <= 99:
        return ["Thunderstorm"]
    return ["Clear"]


def _summarize(temp: float, rain: float, wind: float, conditions: list) -> str:
    parts = [f"{round(temp)}°F"]
    if "Thunderstorm" in conditions:
        parts.append("Thunderstorms")
    elif rain > 0.6:
        parts.append(f"{round(rain * 100)}% rain")
    elif rain > 0.3:
        parts.append(f"{round(rain * 100)}% rain chance")
    if wind > 20:
        parts.append(f"Windy ({round(wind)}mph)")
    if not any(w in conditions for w in ("Rain", "Thunderstorm", "Drizzle")):
        if "Clear" in conditions:
            parts.append("Clear")
        elif "Clouds" in conditions:
            parts.append("Cloudy")
    return " · ".join(parts)
