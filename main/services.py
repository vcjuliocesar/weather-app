import httpx
from asgiref.sync import sync_to_async
from django.utils.timezone import now
from django.conf import settings
from dataclasses import dataclass
from .models import City

@dataclass
class WeatherPayload:
    city: str
    country: str
    current: dict


def _get_city_coordinates(city:str,country:str):
    return City.objects.filter(
        name__iexact=city, 
        country__iexact=country
    ).values("lat","lon").first()

async def fetch_weather(city:str,country:str,ttl=900) -> WeatherPayload:
    
    result = await sync_to_async(_get_city_coordinates)(city,country)
    
    if not result:
        raise ValueError("City not found")
    
    lat = result["lat"]
    lon = result["lon"]
    
    params = {
        "lat": lat,
        "lon": lon,
        "appid": settings.API_TOKEN,
        "units": "metric",
    }
    
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(f"{settings.API}/data/2.5/weather?",params=params)
        resp.raise_for_status()
        data = resp.json()
        
    payload = WeatherPayload(
        city=city.title(),
        country=country.upper(),
        current={
            "dt": data["dt"],
            "temp": data["main"]["temp"],
            "temp_min": data["main"]["temp_min"],
            "temp_max": data["main"]["temp_max"],
            "feels_like": data["main"]["feels_like"],
            "summary": data["weather"][0]["description"].title(),
            "updated_at": now().isoformat(),
        },
    )
    
    return payload