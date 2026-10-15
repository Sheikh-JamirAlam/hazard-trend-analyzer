from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class Location(BaseModel):
    latitude: float
    longitude: float
    label: str | None = None


class AnalysisPeriod(BaseModel):
    start_year: int
    end_year: int


class DataSource(BaseModel):
    name: str
    model: str
    variable: str
    unit: str


class Baseline(BaseModel):
    start_year: int
    end_year: int
    percentile: float
    method: str
    valid_days: int = Field(ge=0)
    expected_days: int = Field(ge=0)
    coverage_percent: float = Field(ge=0, le=100)


class DataQuality(BaseModel):
    expected_days: int = Field(ge=0)
    observed_days: int = Field(ge=0)
    missing_days: int = Field(ge=0)
    excluded_invalid_observations: int = Field(ge=0)


class AnnualMetrics(BaseModel):
    year: int
    event_count: int = Field(ge=0)
    mean_duration_days: float | None = Field(default=None, ge=0)
    max_duration_days: int | None = Field(default=None, ge=0)
    mean_intensity_celsius: float | None = None
    data_available: bool


class SummaryMetrics(BaseModel):
    mean_event_duration_days: float | None = Field(default=None, ge=0)
    mean_event_intensity_celsius: float | None = None


class Insight(BaseModel):
    text: str
    trend_direction: Literal["increasing",
                             "decreasing", "stable", "unavailable"]
    trend_slope_events_per_year: float | None = None


class CacheMetadata(BaseModel):
    hit: bool
    generated_at: datetime | None = None


class HeatwaveAnalysisResponse(BaseModel):
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "location": {"latitude": 28.6, "longitude": 77.2, "label": "Delhi"},
            "period": {"start_year": 2000, "end_year": 2020},
            "data_source": {
                "name": "Open-Meteo Historical Weather API",
                "model": "ERA5 reanalysis",
                "variable": "Daily maximum temperature",
                "unit": "°C",
            },
            "baseline": {
                "start_year": 1981,
                "end_year": 2010,
                "percentile": 95,
                "method": "Empirical percentile across daily maximum temperatures",
                "valid_days": 10957,
                "expected_days": 10957,
                "coverage_percent": 100,
            },
            "threshold_celsius": 40.2,
            "data_quality": {
                "expected_days": 7671,
                "observed_days": 7660,
                "missing_days": 11,
                "excluded_invalid_observations": 0,
            },
            "total_events": 12,
            "summary": {
                "mean_event_duration_days": 3.5,
                "mean_event_intensity_celsius": 1.1,
            },
            "annual_metrics": [{
                "year": 2000,
                "event_count": 1,
                "mean_duration_days": 4.0,
                "max_duration_days": 4,
                "mean_intensity_celsius": 1.1,
                "data_available": True,
            }],
            "insight": {
                "text": "Example only; actual text must be calculated from analyzed data.",
                "trend_direction": "unavailable",
                "trend_slope_events_per_year": None,
            },
            "caveats": ["Example response shape; values are not analysis results."],
            "cache": {"hit": False, "generated_at": None},
        }
    })

    location: Location
    period: AnalysisPeriod
    data_source: DataSource
    baseline: Baseline
    threshold_celsius: float
    data_quality: DataQuality
    total_events: int = Field(ge=0)
    summary: SummaryMetrics
    annual_metrics: list[AnnualMetrics]
    insight: Insight
    caveats: list[str]
    cache: CacheMetadata
