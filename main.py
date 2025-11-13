import os
from typing import List, Optional, Dict, Any

import requests
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Costa Rica Climate API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"message": "Costa Rica Climate API is running"}


# Predefined Costa Rica locations (provinces and key cities)
CR_LOCATIONS = [
    {"name": "San José", "region": "San José", "lat": 9.9281, "lon": -84.0907, "slug": "san-jose"},
    {"name": "Alajuela", "region": "Alajuela", "lat": 10.0163, "lon": -84.2116, "slug": "alajuela"},
    {"name": "Heredia", "region": "Heredia", "lat": 9.9986, "lon": -84.1170, "slug": "heredia"},
    {"name": "Cartago", "region": "Cartago", "lat": 9.8644, "lon": -83.9194, "slug": "cartago"},
    {"name": "Puntarenas", "region": "Puntarenas", "lat": 9.9763, "lon": -84.8384, "slug": "puntarenas"},
    {"name": "Limón", "region": "Limón", "lat": 9.9907, "lon": -83.0360, "slug": "limon"},
    {"name": "Liberia (Guanacaste)", "region": "Guanacaste", "lat": 10.6340, "lon": -85.4377, "slug": "liberia"},
    {"name": "Quepos", "region": "Puntarenas", "lat": 9.4319, "lon": -84.1616, "slug": "quepos"},
    {"name": "Puerto Viejo", "region": "Limón", "lat": 9.6563, "lon": -82.7547, "slug": "puerto-viejo"},
]


@app.get("/api/locations")
def get_locations() -> List[Dict[str, Any]]:
    """Return curated list of Costa Rican locations with coordinates."""
    return CR_LOCATIONS


def fetch_open_meteo(lat: float, lon: float) -> Dict[str, Any]:
    base = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": ",".join([
            "temperature_2m",
            "apparent_temperature",
            "relative_humidity_2m",
            "precipitation",
            "wind_speed_10m",
            "wind_direction_10m",
            "weather_code",
        ]),
        "hourly": ",".join([
            "temperature_2m",
            "precipitation_probability",
            "relative_humidity_2m",
            "cloud_cover",
            "wind_speed_10m",
            "weather_code",
        ]),
        "daily": ",".join([
            "weather_code",
            "temperature_2m_max",
            "temperature_2m_min",
            "precipitation_sum",
            "precipitation_probability_max",
            "sunrise",
            "sunset",
            "wind_speed_10m_max",
        ]),
        "timezone": "auto",
    }
    r = requests.get(base, params=params, timeout=15)
    r.raise_for_status()
    return r.json()


@app.get("/api/weather")
def get_weather(lat: float = Query(...), lon: float = Query(...)) -> Dict[str, Any]:
    """Get current, hourly and daily weather for given coordinates (Costa Rica)."""
    try:
        data = fetch_open_meteo(lat, lon)
        return {"ok": True, "data": data}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@app.get("/api/weather/by-city")
def get_weather_by_city(city: str) -> Dict[str, Any]:
    city_slug = city.lower().replace(" ", "-")
    loc = next((l for l in CR_LOCATIONS if l["slug"] == city_slug), None)
    if not loc:
        return {"ok": False, "error": "City not found", "hint": "Use /api/locations to see options"}
    try:
        data = fetch_open_meteo(loc["lat"], loc["lon"])
        return {"ok": True, "location": loc, "data": data}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@app.get("/api/hello")
def hello():
    return {"message": "Pura vida! Backend listo."}


@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Used",
        "note": "This app fetches live weather data; no DB required.",
    }
    try:
        from database import db  # noqa: F401
        if os.getenv("DATABASE_URL") and os.getenv("DATABASE_NAME"):
            response["database"] = "✅ Available (not required for this app)"
    except Exception:
        pass
    return response


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
