from dataclasses import dataclass
from datetime import date
import math
from typing import Any

import httpx

ARCHIVE_API_URL = "https://archive-api.open-meteo.com/v1/archive"
OPEN_METEO_MODEL = "era5"


class WeatherProviderError(Exception):
    """Base error for provider failures safe to translate at the API layer."""


class WeatherProviderUnavailable(WeatherProviderError):
    pass


class WeatherProviderRateLimited(WeatherProviderError):
    pass


class WeatherProviderInvalidResponse(WeatherProviderError):
    pass


class WeatherDataUnavailable(WeatherProviderError):
    pass


@dataclass(frozen=True)
class DailyTemperature:
    day: date
    maximum_celsius: float | None


@dataclass(frozen=True)
class WeatherResult:
    latitude: float
    longitude: float
    start_date: date
    end_date: date
    temperature_unit: str
    observations: list[DailyTemperature]


class OpenMeteoClient:
    """Fetch daily maximum temperatures from Open-Meteo's historical API."""

    def __init__(
        self,
        client: httpx.AsyncClient | None = None,
        *,
        connect_timeout: float = 5.0,
        read_timeout: float = 30.0,
    ) -> None:
        self._client = client or httpx.AsyncClient(
            timeout=httpx.Timeout(read_timeout, connect=connect_timeout)
        )
        self._owns_client = client is None

    async def close(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    async def fetch_daily_maximum(
        self,
        latitude: float,
        longitude: float,
        start_date: date,
        end_date: date,
    ) -> WeatherResult:
        if start_date > end_date:
            raise ValueError("start_date must be on or before end_date")

        params = {
            "latitude": latitude,
            "longitude": longitude,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "daily": "temperature_2m_max",
            "temperature_unit": "celsius",
            "timezone": "UTC",
            "models": OPEN_METEO_MODEL,
        }

        try:
            response = await self._client.get(ARCHIVE_API_URL, params=params)
        except httpx.TimeoutException as exc:
            raise WeatherProviderUnavailable(
                "Weather provider request timed out") from exc
        except httpx.HTTPError as exc:
            raise WeatherProviderUnavailable(
                "Could not connect to weather provider") from exc

        if response.status_code == 429:
            raise WeatherProviderRateLimited(
                "Weather provider rate limit reached")
        if response.is_error:
            raise WeatherProviderUnavailable(
                f"Weather provider returned HTTP {response.status_code}"
            )

        try:
            payload = response.json()
        except ValueError as exc:
            raise WeatherProviderInvalidResponse(
                "Weather provider returned invalid JSON") from exc

        return self._parse_response(payload, start_date, end_date)

    @staticmethod
    def _parse_response(
        payload: Any,
        requested_start: date,
        requested_end: date,
    ) -> WeatherResult:
        if not isinstance(payload, dict):
            raise WeatherProviderInvalidResponse(
                "Weather provider response must be an object")

        daily = payload.get("daily")
        units = payload.get("daily_units")
        if not isinstance(daily, dict) or not isinstance(units, dict):
            raise WeatherProviderInvalidResponse(
                "Weather provider response is missing daily data or units")

        dates = daily.get("time")
        temperatures = daily.get("temperature_2m_max")
        unit = units.get("temperature_2m_max")
        if not isinstance(dates, list) or not isinstance(temperatures, list):
            raise WeatherProviderInvalidResponse(
                "Weather provider response has invalid daily arrays")
        if len(dates) != len(temperatures):
            raise WeatherProviderInvalidResponse(
                "Date and temperature arrays have different lengths")
        if unit not in {"°C", "°F"}:
            raise WeatherProviderInvalidResponse(
                "Weather provider returned an unsupported temperature unit")
        if unit == "°F":
            raise WeatherProviderInvalidResponse(
                "Expected Celsius temperatures from weather provider")
        if not dates:
            raise WeatherDataUnavailable(
                "No weather observations are available for this period")

        observations: list[DailyTemperature] = []
        try:
            for raw_date, raw_temperature in zip(dates, temperatures, strict=True):
                observation_date = date.fromisoformat(raw_date)
                if raw_temperature is None:
                    temperature = None
                elif isinstance(raw_temperature, bool) or not isinstance(raw_temperature, (int, float)):
                    raise ValueError("Temperature must be numeric or null")
                elif not math.isfinite(raw_temperature):
                    raise ValueError("Temperature must be finite")
                else:
                    temperature = float(raw_temperature)
                observations.append(DailyTemperature(
                    observation_date, temperature))
        except (TypeError, ValueError) as exc:
            raise WeatherProviderInvalidResponse(
                "Weather provider returned invalid dates or temperatures") from exc

        if any(day < requested_start or day > requested_end for day in (o.day for o in observations)):
            raise WeatherProviderInvalidResponse(
                "Weather provider returned dates outside the requested period")

        try:
            latitude = float(payload["latitude"])
            longitude = float(payload["longitude"])
        except (KeyError, TypeError, ValueError) as exc:
            raise WeatherProviderInvalidResponse(
                "Weather provider response is missing coordinates") from exc
        if not math.isfinite(latitude) or not math.isfinite(longitude):
            raise WeatherProviderInvalidResponse(
                "Weather provider returned invalid coordinates")
        if not -90 <= latitude <= 90 or not -180 <= longitude <= 180:
            raise WeatherProviderInvalidResponse(
                "Weather provider returned coordinates outside valid bounds")

        return WeatherResult(
            latitude=latitude,
            longitude=longitude,
            start_date=requested_start,
            end_date=requested_end,
            temperature_unit="°C",
            observations=observations,
        )
