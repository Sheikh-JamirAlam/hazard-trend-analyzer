from datetime import date

from app.services.normalization import normalize_observations
from app.services.weather_provider import DailyTemperature


def test_normalizes_unsorted_data_and_counts_gaps_nulls_and_duplicates() -> None:
    result = normalize_observations(
        [
            DailyTemperature(date(2020, 1, 3), 12.0),
            DailyTemperature(date(2020, 1, 1), 10.0),
            DailyTemperature(date(2020, 1, 1), 11.0),
            DailyTemperature(date(2020, 1, 2), None),
            DailyTemperature(date(2020, 1, 4), 99.0),
        ],
        date(2020, 1, 1),
        date(2020, 1, 4),
    )

    assert [item.day for item in result.observations] == [
        date(2020, 1, 1), date(2020, 1, 2), date(2020, 1, 3), date(2020, 1, 4)
    ]
    assert result.quality.expected_days == 4
    assert result.quality.observed_days == 2
    assert result.quality.missing_days == 2
    assert result.quality.excluded_invalid_observations == 2
