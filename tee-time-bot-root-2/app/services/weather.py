"""
Weather Service
Checks forecast for tee time dates and flags bad weather.
Uses OpenWeather API free tier (1000 calls/day).
"""

import httpx
import logging
from datetime import datetime
from app.config import settings

logger = logging.getLogger(__name__)

OPENWEATHER_URL = "https://api.openweathermap.org/data/2.5/forecast"


async def get_forecast(date: str) -> dict | None:
    """Get weather forecast for a specific date at Chicago location."""
    if not settings.OPENWEATHER_API_KEY:
        return None

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(
                OPENWEATHER_URL,
                params={
                    "lat": settings.HOME_LAT,
                    "lon": settings.HOME_LNG,
                    "appid": settings.OPENWEATHER_API_KEY,
                    "units": "imperial",
                },
            )

            if response.status_code != 200:
                return None

            data = response.json()
            target_date = datetime.strptime(date, "%Y-%m-%d").date()

            # Find forecast entries for the target date morning (6am-12pm)
            morning_forecasts = []
            for entry in data.get("list", []):
                entry_dt = datetime.fromtimestamp(entry["dt"])
                if entry_dt.date() == target_date and 6 <= entry_dt.hour <= 12:
                    morning_forecasts.append(entry)

            if not morning_forecasts:
                return None

            # Average the morning conditions
            avg_temp = sum(f["main"]["temp"] for f in morning_forecasts) / len(morning_forecasts)
            max_rain_chance = max(f.get("pop", 0) for f in morning_forecasts)
            max_wind = max(f["wind"]["speed"] for f in morning_forecasts)
            conditions = [f["weather"][0]["main"] for f in morning_forecasts]

            is_bad = (
                max_rain_chance > 0.6
                or "Thunderstorm" in conditions
                or max_wind > 25
                or avg_temp < 45
            )

            return {
                "date": date,
                "avg_temp_f": round(avg_temp),
                "rain_chance": round(max_rain_chance * 100),
                "max_wind_mph": round(max_wind),
                "conditions": list(set(conditions)),
                "is_bad_weather": is_bad,
                "summary": _summarize(avg_temp, max_rain_chance, max_wind, conditions),
            }

    except Exception as e:
        logger.error("Weather API error: %s", str(e))
        return None


def _summarize(temp: float, rain: float, wind: float, conditions: list) -> str:
    parts = []
    parts.append(f"{round(temp)}°F")

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
