from datetime import date, datetime, timedelta, UTC

import pytest

from app.repositories.analysis_repository import AnalysisRepository, analysis_cache_key
from app.schemas.analysis import (
    AnalysisPeriod,
    AnnualMetrics,
    Baseline,
    CacheMetadata,
    DataQuality,
    DataSource,
    HeatwaveAnalysisResponse,
    Insight,
    Location,
    SummaryMetrics,
)
from app.services.weather_provider import DailyTemperature, WeatherResult


class FakeCollection:
    def __init__(self) -> None:
        self.documents: dict[str, dict] = {}
        self.indexes: list[tuple] = []

    async def create_index(self, keys, **kwargs):
        self.indexes.append((keys, kwargs))

    async def find_one(self, query):
        document = self.documents.get(query["cache_key"])
        if not document:
            return None
        expiry = query.get("expires_at", {}).get("$gt")
        if expiry and document["expires_at"] <= expiry:
            return None
        return document

    async def update_one(self, query, update, upsert=False):
        self.documents[query["cache_key"]] = update["$set"]


class FakeDatabase:
    def __init__(self) -> None:
        self.collections: dict[str, FakeCollection] = {}

    def __getitem__(self, name: str) -> FakeCollection:
        return self.collections.setdefault(name, FakeCollection())


class FakeClient:
    def __init__(self) -> None:
        self.databases: dict[str, FakeDatabase] = {}

    def __getitem__(self, name: str) -> FakeDatabase:
        return self.databases.setdefault(name, FakeDatabase())


def _response() -> HeatwaveAnalysisResponse:
    return HeatwaveAnalysisResponse(
        location=Location(latitude=1, longitude=2, label="Test"),
        period=AnalysisPeriod(start_year=2000, end_year=2001),
        data_source=DataSource(
            name="Open-Meteo", model="ERA5 reanalysis", variable="Daily maximum", unit="°C"
        ),
        baseline=Baseline(
            start_year=1981, end_year=2010, percentile=95, method="linear",
            valid_days=10957, expected_days=10957, coverage_percent=100,
        ),
        threshold_celsius=30,
        data_quality=DataQuality(
            expected_days=731, observed_days=731, missing_days=0,
            excluded_invalid_observations=0,
        ),
        total_events=0,
        summary=SummaryMetrics(),
        annual_metrics=[
            AnnualMetrics(year=2000, event_count=0, data_available=True),
            AnnualMetrics(year=2001, event_count=0, data_available=True),
        ],
        insight=Insight(text="Not enough data", trend_direction="unavailable"),
        caveats=[],
        cache=CacheMetadata(hit=False),
    )


@pytest.mark.asyncio
async def test_weather_and_analysis_cache_hit_miss_and_expiry() -> None:
    repository = AnalysisRepository(FakeClient(), "test")
    await repository.ensure_indexes()
    await repository.ensure_indexes()

    start = date(2020, 1, 1)
    weather = WeatherResult(
        latitude=1,
        longitude=2,
        start_date=start,
        end_date=start,
        temperature_unit="°C",
        observations=[DailyTemperature(start, 25.0)],
    )
    assert await repository.get_weather(1, 2, start, start) is None
    await repository.save_weather(weather, 1, 2)
    cached_weather = await repository.get_weather(1, 2, start, start)
    assert cached_weather is not None
    assert cached_weather.observations == weather.observations

    key = analysis_cache_key(1, 2, 2000, 2001)
    assert await repository.get_analysis(key) is None
    response = _response()
    await repository.save_analysis(key, response)
    cached_analysis = await repository.get_analysis(key)
    assert cached_analysis is not None
    assert cached_analysis.cache.hit
    assert cached_analysis.total_events == response.total_events

    expired = datetime.now(UTC) - timedelta(days=1)
    repository._analyses.documents[key]["expires_at"] = expired
    assert await repository.get_analysis(key) is None
