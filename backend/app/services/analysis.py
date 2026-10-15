from __future__ import annotations

from datetime import UTC, date, datetime
import asyncio
import math
from typing import TYPE_CHECKING

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
from app.services.heatwave import (
    BASELINE_END_YEAR,
    BASELINE_PERCENTILE,
    BASELINE_START_YEAR,
    HeatwaveEvent,
    calculate_threshold,
    detect_heatwaves,
)
from app.services.normalization import NormalizedWeather, normalize_observations
from app.services.weather_provider import WeatherResult

if TYPE_CHECKING:
    from app.repositories.analysis_repository import AnalysisRepository
    from app.services.weather_provider import OpenMeteoClient


def _trend_slope(annual: list[AnnualMetrics]) -> float | None:
    points = [(metric.year, metric.event_count)
              for metric in annual if metric.data_available]
    if len(points) < 2:
        return None
    x_mean = sum(year for year, _ in points) / len(points)
    y_mean = sum(value for _, value in points) / len(points)
    denominator = sum((year - x_mean) ** 2 for year, _ in points)
    return sum((year - x_mean) * (value - y_mean) for year, value in points) / denominator


def _annual_metrics(
    normalized: NormalizedWeather,
    events: list[HeatwaveEvent],
    start_year: int,
    end_year: int,
) -> list[AnnualMetrics]:
    output: list[AnnualMetrics] = []
    events_by_start_year: dict[int, list[HeatwaveEvent]] = {}
    for event in events:
        events_by_start_year.setdefault(
            event.start_date.year, []).append(event)

    observed_by_year: dict[int, int] = {}
    for observation in normalized.observations:
        if observation.maximum_celsius is not None:
            observed_by_year[observation.day.year] = observed_by_year.get(
                observation.day.year, 0) + 1

    for year in range(start_year, end_year + 1):
        yearly_events = events_by_start_year.get(year, [])
        durations = [event.duration_days for event in yearly_events]
        intensities = [event.mean_excess_celsius for event in yearly_events]
        output.append(
            AnnualMetrics(
                year=year,
                event_count=len(yearly_events),
                mean_duration_days=round(
                    sum(durations) / len(durations), 2) if durations else None,
                max_duration_days=max(durations) if durations else None,
                mean_intensity_celsius=round(
                    sum(intensities) / len(intensities), 2) if intensities else None,
                data_available=observed_by_year.get(year, 0) > 0,
            )
        )
    return output


def _make_insight(annual: list[AnnualMetrics]) -> Insight:
    slope = _trend_slope(annual)
    if slope is None:
        return Insight(
            text="There is not enough annual data to estimate a trend.",
            trend_direction="unavailable",
        )
    if math.isclose(slope, 0.0, abs_tol=0.01):
        direction = "stable"
        description = "The fitted linear trend is approximately flat"
    elif slope > 0:
        direction = "increasing"
        description = "The fitted linear trend is increasing"
    else:
        direction = "decreasing"
        description = "The fitted linear trend is decreasing"
    return Insight(
        text=f"{description} by {abs(slope):.2f} events per year across years with observations.",
        trend_direction=direction,
        trend_slope_events_per_year=round(slope, 4),
    )


def build_response(
    *,
    latitude: float,
    longitude: float,
    location_label: str | None,
    start_year: int,
    end_year: int,
    weather: WeatherResult,
    baseline_weather: WeatherResult,
    cache_hit: bool = False,
) -> HeatwaveAnalysisResponse:
    period_start = date(start_year, 1, 1)
    period_end = date(end_year, 12, 31)
    if end_year == date.today().year:
        period_end = date.today()
    normalized = normalize_observations(
        weather.observations, period_start, period_end)
    normalized_baseline = normalize_observations(
        baseline_weather.observations,
        date(BASELINE_START_YEAR, 1, 1),
        date(BASELINE_END_YEAR, 12, 31),
    )
    threshold = calculate_threshold(normalized_baseline.observations)
    events = detect_heatwaves(normalized.observations, threshold)
    annual = _annual_metrics(normalized, events, start_year, end_year)
    summary = SummaryMetrics(
        mean_event_duration_days=(
            round(sum(event.duration_days for event in events) / len(events), 2)
            if events else None
        ),
        mean_event_intensity_celsius=(
            round(sum(event.mean_excess_celsius for event in events) / len(events), 2)
            if events else None
        ),
    )

    caveats: list[str] = [
        "ERA5 is a gridded reanalysis estimate informed by observations and weather models, not a single local weather-station record.",
        "The threshold is the empirical 95th percentile across all daily maximum temperatures from 1981–2010, using linear interpolation.",
        "The threshold pools all baseline calendar days; it is not adjusted for season or day of year.",
        "Events require at least three consecutive days strictly above the threshold; an event crossing years is assigned to its start year.",
        "Events are evaluated within the selected date window; runs are clipped at its start and end.",
        "Intensity is the event mean daily excess above the threshold in °C. The fitted trend is descriptive and does not establish causation.",
    ]
    if normalized.quality.missing_days:
        caveats.append(
            f"{normalized.quality.missing_days} selected-period days are missing or have null temperatures; gaps break event runs."
        )
    if normalized_baseline.quality.missing_days:
        baseline_coverage = normalized_baseline.quality.observed_days / \
            normalized_baseline.quality.expected_days * 100
        caveats.append(
            f"The 1981–2010 baseline contains {baseline_coverage:.1f}% valid daily observations."
        )
    if end_year == date.today().year and period_end < date(end_year, 12, 31):
        caveats.append(
            f"The final year is partial through {period_end.isoformat()}."
        )
        caveats.append(
            "Recent ERA5 dates may not yet be available because the reanalysis is updated with a delay."
        )
    if len(annual) < 10:
        caveats.append(
            "The selected period is shorter than 10 years; trend estimates may be unstable.")

    return HeatwaveAnalysisResponse(
        location=Location(latitude=latitude,
                          longitude=longitude, label=location_label),
        period=AnalysisPeriod(start_year=start_year, end_year=end_year),
        data_source=DataSource(
            name="Open-Meteo Historical Weather API",
            model="ERA5 reanalysis",
            variable="Daily maximum temperature",
            unit="°C",
        ),
        baseline=Baseline(
            start_year=BASELINE_START_YEAR,
            end_year=BASELINE_END_YEAR,
            percentile=BASELINE_PERCENTILE,
            method="Empirical percentile across daily maximum temperatures using linear interpolation",
            valid_days=normalized_baseline.quality.observed_days,
            expected_days=normalized_baseline.quality.expected_days,
            coverage_percent=round(
                normalized_baseline.quality.observed_days
                / normalized_baseline.quality.expected_days
                * 100,
                2,
            ),
        ),
        threshold_celsius=round(threshold, 2),
        data_quality=DataQuality(
            expected_days=normalized.quality.expected_days,
            observed_days=normalized.quality.observed_days,
            missing_days=normalized.quality.missing_days,
            excluded_invalid_observations=normalized.quality.excluded_invalid_observations,
        ),
        total_events=len(events),
        summary=summary,
        annual_metrics=annual,
        insight=_make_insight(annual),
        caveats=caveats,
        cache=CacheMetadata(hit=cache_hit),
    )


class HeatwaveAnalysisService:
    def __init__(self, provider: OpenMeteoClient, repository: AnalysisRepository) -> None:
        self._provider = provider
        self._repository = repository

    async def analyze(
        self,
        latitude: float,
        longitude: float,
        start_year: int,
        end_year: int,
        location_label: str | None = None,
    ) -> HeatwaveAnalysisResponse:
        from app.repositories.analysis_repository import analysis_cache_key

        key = analysis_cache_key(latitude, longitude, start_year, end_year)
        cached = await self._repository.get_analysis(key)
        if cached is not None:
            return cached.model_copy(
                update={
                    "location": Location(
                        latitude=latitude,
                        longitude=longitude,
                        label=location_label,
                    )
                }
            )

        today = date.today()
        start = date(start_year, 1, 1)
        end = min(date(end_year, 12, 31), today)
        baseline_start = date(BASELINE_START_YEAR, 1, 1)
        baseline_end = date(BASELINE_END_YEAR, 12, 31)

        await self._repository.ensure_indexes()
        weather, baseline = await asyncio.gather(
            self._load_weather(latitude, longitude, start, end),
            self._load_weather(latitude, longitude,
                               baseline_start, baseline_end),
        )
        response = build_response(
            latitude=latitude,
            longitude=longitude,
            location_label=location_label,
            start_year=start_year,
            end_year=end_year,
            weather=weather,
            baseline_weather=baseline,
        )
        response = response.model_copy(
            update={"cache": CacheMetadata(
                hit=False, generated_at=datetime.now(UTC))}
        )
        await self._repository.save_analysis(key, response)
        return response

    async def _load_weather(
        self, latitude: float, longitude: float, start: date, end: date
    ) -> WeatherResult:
        result = await self._repository.get_weather(latitude, longitude, start, end)
        if result is not None:
            return result
        result = await self._provider.fetch_daily_maximum(latitude, longitude, start, end)
        await self._repository.save_weather(result, latitude, longitude)
        return result
