from datetime import date
from collections import defaultdict, deque
from time import monotonic
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, Request
from pymongo.errors import PyMongoError

from app.schemas.analysis import HeatwaveAnalysisResponse
from app.services.analysis import HeatwaveAnalysisService
from app.services.heatwave import InsufficientBaselineData
from app.services.weather_provider import (
    OpenMeteoClient,
    WeatherDataUnavailable,
    WeatherProviderInvalidResponse,
    WeatherProviderRateLimited,
    WeatherProviderUnavailable,
)

router = APIRouter(prefix="/analysis", tags=["analysis"])
MAX_ANALYSIS_YEARS = 40
_REQUESTS: dict[str, deque[float]] = defaultdict(deque)
_RATE_LIMIT = 30
_RATE_WINDOW_SECONDS = 60


@router.get(
    "/heatwaves",
    response_model=HeatwaveAnalysisResponse,
    responses={
        400: {"description": "Invalid year range"},
        422: {"description": "Invalid query parameters"},
        404: {"description": "No weather data is available"},
        429: {"description": "Analysis request rate limit reached"},
        502: {"description": "Weather provider failure"},
        503: {"description": "Database or weather provider is unavailable"},
    },
    summary="Analyze historical heatwave trends",
    description=(
        "Returns annual heatwave metrics for a coordinate and year range. "
        "A heatwave is at least three consecutive days above the baseline "
        "95th-percentile daily maximum temperature."
    ),
)
async def analyze_heatwaves(
    request: Request,
    latitude: Annotated[float, Query(ge=-90, le=90, allow_inf_nan=False)],
    longitude: Annotated[float, Query(ge=-180, le=180, allow_inf_nan=False)],
    start_year: Annotated[int, Query(ge=1940)],
    end_year: Annotated[int, Query(ge=1940)],
    location_label: Annotated[str | None, Query(max_length=100)] = None,
) -> HeatwaveAnalysisResponse:
    current_year = date.today().year
    if start_year > end_year:
        raise HTTPException(
            status_code=400, detail="start_year must be less than or equal to end_year")
    if end_year > current_year:
        raise HTTPException(
            status_code=400, detail="Future analysis years are not supported")
    if end_year - start_year + 1 > MAX_ANALYSIS_YEARS:
        raise HTTPException(
            status_code=400,
            detail=f"The analysis period cannot exceed {MAX_ANALYSIS_YEARS} years",
        )

    now = monotonic()
    client_ip = request.client.host if request.client else "unknown"
    request_times = _REQUESTS[client_ip]
    while request_times and now - request_times[0] >= _RATE_WINDOW_SECONDS:
        request_times.popleft()
    if len(request_times) >= _RATE_LIMIT:
        raise HTTPException(
            status_code=429, detail="Too many analysis requests. Try again in a minute.")
    request_times.append(now)

    provider = OpenMeteoClient(client=request.app.state.http_client)
    service = HeatwaveAnalysisService(
        provider, request.app.state.analysis_repository)
    try:
        return await service.analyze(
            latitude, longitude, start_year, end_year, location_label
        )
    except InsufficientBaselineData as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except WeatherDataUnavailable as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except WeatherProviderRateLimited as exc:
        raise HTTPException(
            status_code=503, detail="Weather provider is rate limited; retry later") from exc
    except (WeatherProviderInvalidResponse, WeatherProviderUnavailable) as exc:
        raise HTTPException(
            status_code=502, detail="Weather provider could not complete the analysis") from exc
    except PyMongoError as exc:
        raise HTTPException(
            status_code=503, detail="Analysis storage is unavailable; retry later") from exc
