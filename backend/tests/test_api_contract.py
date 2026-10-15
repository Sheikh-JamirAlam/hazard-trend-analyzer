from datetime import date

from fastapi.testclient import TestClient

from app.main import app


def test_health_and_openapi_contract() -> None:
    with TestClient(app) as client:
        assert client.get("/api/health").json() == {"status": "ok"}
        schema = client.get("/openapi.json").json()

    operation = schema["paths"]["/api/analysis/heatwaves"]["get"]
    assert operation["responses"]["200"]["content"]["application/json"]["schema"]["$ref"].endswith(
        "HeatwaveAnalysisResponse"
    )


def test_query_validation_rejects_invalid_coordinates_and_periods() -> None:
    with TestClient(app) as client:
        invalid_coordinate = client.get(
            "/api/analysis/heatwaves",
            params={"latitude": 91, "longitude": 0,
                    "start_year": 2000, "end_year": 2001},
        )
        reversed_period = client.get(
            "/api/analysis/heatwaves",
            params={"latitude": 0, "longitude": 0,
                    "start_year": 2001, "end_year": 2000},
        )
        too_long = client.get(
            "/api/analysis/heatwaves",
            params={"latitude": 0, "longitude": 0,
                    "start_year": 1980, "end_year": 2020},
        )
        future_period = client.get(
            "/api/analysis/heatwaves",
            params={
                "latitude": 0,
                "longitude": 0,
                "start_year": date.today().year,
                "end_year": date.today().year + 1,
            },
        )

    assert invalid_coordinate.status_code == 422
    assert reversed_period.status_code == 400
    assert too_long.status_code == 400
    assert future_period.status_code == 400
