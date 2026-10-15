from datetime import UTC, date, datetime, timedelta
import hashlib

from pymongo import ASCENDING, AsyncMongoClient

from app.schemas.analysis import CacheMetadata, HeatwaveAnalysisResponse, Location
from app.services.weather_provider import DailyTemperature, WeatherResult

PROVIDER_VERSION = "open-meteo-archive-era5-v1"
ALGORITHM_VERSION = "heatwave-era5-p95-1981-2010-v1"
ANALYSIS_TTL = timedelta(hours=24)
WEATHER_TTL = timedelta(days=30)


def weather_cache_key(latitude: float, longitude: float, start: date, end: date) -> str:
    return f"{PROVIDER_VERSION}:{latitude:.5f}:{longitude:.5f}:{start}:{end}"


def analysis_cache_key(latitude: float, longitude: float, start_year: int, end_year: int) -> str:
    key = f"{ALGORITHM_VERSION}:{latitude:.5f}:{longitude:.5f}:{start_year}:{end_year}"
    return hashlib.sha256(key.encode()).hexdigest()


class AnalysisRepository:
    def __init__(self, client: AsyncMongoClient, database_name: str) -> None:
        database = client[database_name]
        self._weather = database["weather_cache"]
        self._analyses = database["analysis_cache"]
        self._indexes_ready = False

    async def ensure_indexes(self) -> None:
        if self._indexes_ready:
            return
        await self._weather.create_index([("cache_key", ASCENDING)], unique=True)
        await self._weather.create_index([("expires_at", ASCENDING)], expireAfterSeconds=0)
        await self._analyses.create_index([("cache_key", ASCENDING)], unique=True)
        await self._analyses.create_index([("expires_at", ASCENDING)], expireAfterSeconds=0)
        self._indexes_ready = True

    async def get_weather(
        self, latitude: float, longitude: float, start: date, end: date
    ) -> WeatherResult | None:
        key = weather_cache_key(latitude, longitude, start, end)
        doc = await self._weather.find_one({"cache_key": key, "expires_at": {"$gt": datetime.now(UTC)}})
        if not doc:
            return None
        return WeatherResult(
            latitude=doc["latitude"],
            longitude=doc["longitude"],
            start_date=start,
            end_date=end,
            temperature_unit="°C",
            observations=[
                DailyTemperature(date.fromisoformat(
                    item["day"]), item["maximum_celsius"])
                for item in doc["observations"]
            ],
        )

    async def save_weather(
        self, result: WeatherResult, requested_latitude: float, requested_longitude: float
    ) -> None:
        key = weather_cache_key(
            requested_latitude, requested_longitude, result.start_date, result.end_date)
        await self._weather.update_one(
            {"cache_key": key},
            {
                "$set": {
                    "cache_key": key,
                    "provider": PROVIDER_VERSION,
                    "requested_latitude": requested_latitude,
                    "requested_longitude": requested_longitude,
                    "latitude": result.latitude,
                    "longitude": result.longitude,
                    "start_date": result.start_date.isoformat(),
                    "end_date": result.end_date.isoformat(),
                    "observations": [
                        {"day": item.day.isoformat(
                        ), "maximum_celsius": item.maximum_celsius}
                        for item in result.observations
                    ],
                    "stored_at": datetime.now(UTC),
                    "expires_at": datetime.now(UTC) + WEATHER_TTL,
                }
            },
            upsert=True,
        )

    async def get_analysis(self, key: str) -> HeatwaveAnalysisResponse | None:
        doc = await self._analyses.find_one({"cache_key": key, "expires_at": {"$gt": datetime.now(UTC)}})
        if not doc:
            return None
        response = HeatwaveAnalysisResponse.model_validate(doc["response"])
        return response.model_copy(
            update={
                "location": Location(
                    latitude=response.location.latitude,
                    longitude=response.location.longitude,
                    label=response.location.label,
                ),
                "cache": CacheMetadata(hit=True, generated_at=doc["generated_at"]),
            }
        )

    async def save_analysis(self, key: str, response: HeatwaveAnalysisResponse) -> None:
        generated_at = datetime.now(UTC)
        await self._analyses.update_one(
            {"cache_key": key},
            {
                "$set": {
                    "cache_key": key,
                    "algorithm": ALGORITHM_VERSION,
                    "response": response.model_dump(mode="json"),
                    "generated_at": generated_at,
                    "expires_at": generated_at + ANALYSIS_TTL,
                }
            },
            upsert=True,
        )
