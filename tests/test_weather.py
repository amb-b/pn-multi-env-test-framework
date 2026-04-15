"""
Weather API test suite.

Targets: https://api.open-meteo.com/v1/forecast
Environment config is injected via the `weather_env` fixture (conftest.py).
City parametrization data comes from test_data/cities.json (injected via `cities` fixture).
All thresholds come from config/environments.yaml — zero hardcoded values.

Test coverage:
  1. Forecast endpoint reachability for each city (HTTP 200)
  2. Response time gate (< max_response_time from YAML)
  3. Temperature range validation (-80 to 60°C from YAML)
  4. Hourly entry count > 0
  5. Timezone field present and non-empty
"""
from __future__ import annotations

import json
from typing import Any, Dict, List

import allure
import pytest
import requests

from src.validators.weather_validator import WeatherForecastValidator

# ---------------------------------------------------------------------------
# Module marker
# ---------------------------------------------------------------------------
pytestmark = [pytest.mark.weather]


# ---------------------------------------------------------------------------
# Parametrize helper — IDs come from city names for readable test output
# ---------------------------------------------------------------------------

def _city_id(city: Dict[str, Any]) -> str:
    return city["name"].replace(" ", "_")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _build_forecast_params(city: Dict[str, Any], env_cfg: Dict[str, Any]) -> Dict[str, Any]:
    """Build query parameters from city data and YAML env config."""
    params = env_cfg.get("params", {})
    return {
        "latitude": city["latitude"],
        "longitude": city["longitude"],
        "hourly": params.get("hourly", "temperature_2m"),
        "timezone": params.get("timezone", "auto"),
    }


def _get_forecast(
    session: requests.Session,
    base_url: str,
    city: Dict[str, Any],
    env_cfg: Dict[str, Any],
) -> requests.Response:
    """Call the forecast endpoint for a given city."""
    url = f"{base_url}/forecast"
    params = _build_forecast_params(city, env_cfg)
    return session.get(url, params=params, timeout=15)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@allure.epic("Weather API")
@allure.feature("Forecast endpoint")
class TestWeatherForecast:
    """Parametrized forecast tests — one test instance per city."""

    @allure.story("HTTP reachability")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.parametrize("city", pytest.lazy_fixture("cities") if False else [], ids=[])
    def _placeholder(self) -> None:  # replaced by parametrize below
        pass

    # Real parametrize wired up via indirect fixture (avoids calling fixture at
    # collection time before cities.json is available).  We use a module-level
    # function instead.
    pass


# Module-level parametrized functions (preferred over class methods for
# parametrize + fixtures, per framework-rules.md)

def _city_params() -> List[Dict[str, Any]]:
    """Load cities at collection time for parametrize IDs."""
    import json
    from pathlib import Path
    cities_path = Path(__file__).parent.parent / "test_data" / "cities.json"
    with cities_path.open() as fh:
        return json.load(fh)


_CITIES = _city_params()


@allure.epic("Weather API")
@allure.feature("Forecast endpoint")
@allure.story("HTTP 200 and response time")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.parametrize("city", _CITIES, ids=[c["name"] for c in _CITIES])
def test_forecast_returns_200(
    city: Dict[str, Any],
    http_session: requests.Session,
    weather_env: Dict[str, Any],
) -> None:
    """Each city's forecast endpoint returns HTTP 200 within the time threshold."""
    base_url = weather_env["base_url"]
    max_rt = weather_env["max_response_time"]

    allure.dynamic.tag(city["name"])
    allure.dynamic.parameter("city", city["name"])

    with allure.step(f"GET /v1/forecast for {city['name']}"):
        resp = _get_forecast(http_session, base_url, city, weather_env)

    with allure.step("Assert HTTP 200"):
        assert resp.status_code == 200, (
            f"Expected 200 for {city['name']}, got {resp.status_code}: {resp.text[:200]}"
        )

    with allure.step(f"Assert response time < {max_rt}s"):
        elapsed = resp.elapsed.total_seconds()
        assert elapsed < max_rt, (
            f"{city['name']}: response took {elapsed:.2f}s, threshold is {max_rt}s"
        )


@allure.epic("Weather API")
@allure.feature("Forecast endpoint")
@allure.story("Temperature range validation")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.parametrize("city", _CITIES, ids=[c["name"] for c in _CITIES])
def test_forecast_temperature_range(
    city: Dict[str, Any],
    http_session: requests.Session,
    weather_env: Dict[str, Any],
) -> None:
    """All temperature readings are within the physically reasonable range."""
    base_url = weather_env["base_url"]
    max_rt = weather_env["max_response_time"]

    temp_range = weather_env.get("temperature_range", {})
    temp_min: float = temp_range.get("min", -80)
    temp_max: float = temp_range.get("max", 60)

    allure.dynamic.parameter("city", city["name"])
    allure.dynamic.parameter("temp_min", temp_min)
    allure.dynamic.parameter("temp_max", temp_max)

    with allure.step(f"GET forecast for {city['name']}"):
        resp = _get_forecast(http_session, base_url, city, weather_env)

    assert resp.status_code == 200
    assert resp.elapsed.total_seconds() < max_rt

    data = resp.json()

    with allure.step(f"Validate temperatures in [{temp_min}, {temp_max}]°C"):
        validator = WeatherForecastValidator(data, temp_min=temp_min, temp_max=temp_max)
        validator.validate()

        if validator.errors:
            error_summary = "\n".join(str(e) for e in validator.errors)
            allure.attach(
                error_summary,
                name="Temperature range failures",
                attachment_type=allure.attachment_type.TEXT,
            )
            pytest.fail(
                f"{city['name']}: {len(validator.errors)} temperature validation failures"
            )


@allure.epic("Weather API")
@allure.feature("Forecast endpoint")
@allure.story("Hourly entry count")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.parametrize("city", _CITIES, ids=[c["name"] for c in _CITIES])
def test_forecast_hourly_count_positive(
    city: Dict[str, Any],
    http_session: requests.Session,
    weather_env: Dict[str, Any],
) -> None:
    """Forecast response contains at least one hourly temperature entry."""
    base_url = weather_env["base_url"]
    min_results = weather_env["min_results_count"]

    allure.dynamic.parameter("city", city["name"])

    with allure.step(f"GET forecast for {city['name']}"):
        resp = _get_forecast(http_session, base_url, city, weather_env)

    assert resp.status_code == 200

    data = resp.json()
    validator = WeatherForecastValidator(data)

    hourly_count = validator.hourly_count()
    allure.attach(
        f"{city['name']}: {hourly_count} hourly entries",
        name="Hourly count",
        attachment_type=allure.attachment_type.TEXT,
    )

    with allure.step(f"Assert hourly count >= {min_results}"):
        assert hourly_count >= min_results, (
            f"{city['name']}: expected >= {min_results} hourly entries, got {hourly_count}"
        )


@allure.epic("Weather API")
@allure.feature("Forecast endpoint")
@allure.story("Timezone field present")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.parametrize("city", _CITIES, ids=[c["name"] for c in _CITIES])
def test_forecast_timezone_field_present(
    city: Dict[str, Any],
    http_session: requests.Session,
    weather_env: Dict[str, Any],
) -> None:
    """Forecast response includes a non-empty timezone field."""
    base_url = weather_env["base_url"]
    max_rt = weather_env["max_response_time"]

    allure.dynamic.parameter("city", city["name"])

    with allure.step(f"GET forecast for {city['name']}"):
        resp = _get_forecast(http_session, base_url, city, weather_env)

    assert resp.status_code == 200
    assert resp.elapsed.total_seconds() < max_rt

    data = resp.json()
    validator = WeatherForecastValidator(data)
    # Only run timezone validation
    validator._validate_timezone()

    tz = validator.timezone()
    allure.attach(
        f"{city['name']}: timezone = {tz!r}",
        name="Timezone value",
        attachment_type=allure.attachment_type.TEXT,
    )

    with allure.step("Assert timezone is present and non-empty"):
        if validator.errors:
            pytest.fail(f"{city['name']}: timezone validation failed — {validator.errors[0]}")

        assert tz, f"{city['name']}: timezone field is empty or missing"


@allure.epic("Weather API")
@allure.feature("Forecast endpoint")
@allure.story("Full schema validation")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.parametrize("city", _CITIES, ids=[c["name"] for c in _CITIES])
def test_forecast_full_schema(
    city: Dict[str, Any],
    http_session: requests.Session,
    weather_env: Dict[str, Any],
) -> None:
    """Run the complete WeatherForecastValidator schema check for each city."""
    base_url = weather_env["base_url"]
    max_rt = weather_env["max_response_time"]

    temp_range = weather_env.get("temperature_range", {})
    temp_min: float = temp_range.get("min", -80)
    temp_max: float = temp_range.get("max", 60)

    allure.dynamic.parameter("city", city["name"])

    resp = _get_forecast(http_session, base_url, city, weather_env)
    assert resp.status_code == 200
    assert resp.elapsed.total_seconds() < max_rt

    data = resp.json()
    allure.attach(
        json.dumps({k: v for k, v in data.items() if k != "hourly"}, indent=2),
        name=f"{city['name']} response metadata",
        attachment_type=allure.attachment_type.JSON,
    )

    validator = WeatherForecastValidator(data, temp_min=temp_min, temp_max=temp_max)
    validator.assert_valid()
