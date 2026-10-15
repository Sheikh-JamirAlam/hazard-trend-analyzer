from datetime import date

import httpx
import pytest

from app.services.weather_provider import (
    OpenMeteoClient,
    WeatherDataUnavailable,
    WeatherProviderInvalidResponse,
    WeatherProviderRateLimited,
    WeatherProviderUnavailable,
)


@pytest.mark.asyncio
async def test_fetches_and_translates_daily_max_temperatures() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.params["daily"] == "temperature_2m_max"
        assert request.url.params["temperature_unit"] == "celsius"
        assert request.url.params["models"] == "era5"
        return httpx.Response(200, json={
            "latitude": 28.5,
            "longitude": 77.0,
            "daily_units": {"temperature_2m_max": "°C"},
            "daily": {"time": ["2020-01-01"], "temperature_2m_max": [20.5]},
        })

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http:
        result = await OpenMeteoClient(http).fetch_daily_maximum(
            28.6, 77.2, date(2020, 1, 1), date(2020, 1, 1)
        )
    assert result.observations[0].maximum_celsius == 20.5


@pytest.mark.asyncio
async def test_rate_limit_and_malformed_payload_are_explicit() -> None:
    async def limited(request: httpx.Request) -> httpx.Response:
        return httpx.Response(429)

    async with httpx.AsyncClient(transport=httpx.MockTransport(limited)) as http:
        with pytest.raises(WeatherProviderRateLimited):
            await OpenMeteoClient(http).fetch_daily_maximum(
                0, 0, date(2020, 1, 1), date(2020, 1, 1)
            )

    async def malformed(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"daily": [], "daily_units": {}})

    async with httpx.AsyncClient(transport=httpx.MockTransport(malformed)) as http:
        with pytest.raises(WeatherProviderInvalidResponse):
            await OpenMeteoClient(http).fetch_daily_maximum(
                0, 0, date(2020, 1, 1), date(2020, 1, 1)
            )


@pytest.mark.asyncio
async def test_empty_data_null_temperatures_and_upstream_failure() -> None:
    async def empty(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={
            "latitude": 0,
            "longitude": 0,
            "daily_units": {"temperature_2m_max": "°C"},
            "daily": {"time": [], "temperature_2m_max": []},
        })

    async with httpx.AsyncClient(transport=httpx.MockTransport(empty)) as http:
        with pytest.raises(WeatherDataUnavailable):
            await OpenMeteoClient(http).fetch_daily_maximum(
                0, 0, date(2020, 1, 1), date(2020, 1, 1)
            )

    async def null_value(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={
            "latitude": 0,
            "longitude": 0,
            "daily_units": {"temperature_2m_max": "°C"},
            "daily": {"time": ["2020-01-01"], "temperature_2m_max": [None]},
        })

    async with httpx.AsyncClient(transport=httpx.MockTransport(null_value)) as http:
        result = await OpenMeteoClient(http).fetch_daily_maximum(
            0, 0, date(2020, 1, 1), date(2020, 1, 1)
        )
        assert result.observations[0].maximum_celsius is None

    async def upstream_error(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503)

    async with httpx.AsyncClient(transport=httpx.MockTransport(upstream_error)) as http:
        with pytest.raises(WeatherProviderUnavailable):
            await OpenMeteoClient(http).fetch_daily_maximum(
                0, 0, date(2020, 1, 1), date(2020, 1, 1)
            )


@pytest.mark.asyncio
async def test_timeout_is_reported_as_provider_unavailable() -> None:
    async def timeout(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("slow", request=request)

    async with httpx.AsyncClient(transport=httpx.MockTransport(timeout)) as http:
        with pytest.raises(WeatherProviderUnavailable, match="timed out"):
            await OpenMeteoClient(http).fetch_daily_maximum(
                0, 0, date(2020, 1, 1), date(2020, 1, 1)
            )
