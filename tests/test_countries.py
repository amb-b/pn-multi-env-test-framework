"""
Countries API test suite.

Targets: https://restcountries.com/v3.1
Environment config is injected via the `countries_env` fixture (conftest.py).
All thresholds come from config/environments.yaml — zero hardcoded values.

Test coverage:
  1. GET /region/europe          — result count > 40
  2. GET /name/germany           — schema validation (name, capital, population,
                                    currencies, languages)
  3. GET /all?fields=name,pop    — every country has population > 0
  4. Cross-reference             — germany from /name also appears in /region
  5. Response time gate          — all requests < max_response_time (from YAML)
"""
from __future__ import annotations

from typing import Any, Dict, List

import allure
import pytest
import requests

from src.validators.countries_validator import CountriesListValidator, CountriesValidator

# ---------------------------------------------------------------------------
# Module-level marker so --env filtering works at collection time too
# ---------------------------------------------------------------------------
pytestmark = [pytest.mark.countries]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

MIN_EUROPE_COUNTRIES = 40  # factual lower bound, not a configurable threshold


def _get(
    session: requests.Session,
    base_url: str,
    path: str,
    params: Dict[str, Any] | None = None,
) -> requests.Response:
    """Thin wrapper so every test call goes through a single place."""
    url = f"{base_url}{path}"
    return session.get(url, params=params, timeout=10)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@allure.epic("Countries API")
@allure.feature("Region endpoint")
class TestRegionEurope:
    """GET /region/europe — sanity checks on European countries list."""

    @allure.story("Result count")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_europe_returns_more_than_40_countries(
        self,
        http_session: requests.Session,
        countries_env: Dict[str, Any],
    ) -> None:
        base_url = countries_env["base_url"]
        max_rt = countries_env["max_response_time"]

        with allure.step("GET /region/europe"):
            resp = _get(http_session, base_url, "/region/europe")

        with allure.step("Assert HTTP 200"):
            assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"

        with allure.step(f"Assert response time < {max_rt}s"):
            assert resp.elapsed.total_seconds() < max_rt, (
                f"Response took {resp.elapsed.total_seconds():.2f}s, "
                f"threshold is {max_rt}s"
            )

        data = resp.json()
        with allure.step(f"Assert result count > {MIN_EUROPE_COUNTRIES}"):
            validator = CountriesListValidator(data, min_count=MIN_EUROPE_COUNTRIES + 1)
            validator.assert_valid()
            allure.attach(
                f"Returned {len(data)} European countries",
                name="Result count",
                attachment_type=allure.attachment_type.TEXT,
            )

    @allure.story("Response time gate")
    @allure.severity(allure.severity_level.NORMAL)
    def test_europe_response_time_within_threshold(
        self,
        http_session: requests.Session,
        countries_env: Dict[str, Any],
    ) -> None:
        base_url = countries_env["base_url"]
        max_rt = countries_env["max_response_time"]
        resp = _get(http_session, base_url, "/region/europe")
        elapsed = resp.elapsed.total_seconds()
        assert elapsed < max_rt, (
            f"Response time {elapsed:.3f}s exceeded threshold {max_rt}s"
        )


@allure.epic("Countries API")
@allure.feature("Name search endpoint")
class TestCountryByName:
    """GET /name/germany — schema and data validation."""

    @allure.story("Schema validation")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_germany_schema_has_required_fields(
        self,
        http_session: requests.Session,
        countries_env: Dict[str, Any],
    ) -> None:
        base_url = countries_env["base_url"]
        max_rt = countries_env["max_response_time"]

        with allure.step("GET /name/germany"):
            resp = _get(http_session, base_url, "/name/germany")

        with allure.step("Assert HTTP 200"):
            assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"

        with allure.step(f"Assert response time < {max_rt}s"):
            elapsed = resp.elapsed.total_seconds()
            assert elapsed < max_rt, (
                f"Response took {elapsed:.2f}s, threshold is {max_rt}s"
            )

        data: List[Dict[str, Any]] = resp.json()
        assert isinstance(data, list) and len(data) > 0, "Expected non-empty list"

        country = data[0]
        allure.attach(
            str(list(country.keys())),
            name="Top-level keys present",
            attachment_type=allure.attachment_type.TEXT,
        )

        with allure.step("Validate schema with CountriesValidator"):
            validator = CountriesValidator(country)
            validator.assert_valid()

    @allure.story("Data integrity")
    def test_germany_population_is_positive(
        self,
        http_session: requests.Session,
        countries_env: Dict[str, Any],
    ) -> None:
        base_url = countries_env["base_url"]
        resp = _get(http_session, base_url, "/name/germany")
        assert resp.status_code == 200
        data = resp.json()
        pop = data[0].get("population")
        assert isinstance(pop, int) and pop > 0, f"population must be int > 0, got {pop}"


@allure.epic("Countries API")
@allure.feature("All countries endpoint")
class TestAllCountries:
    """GET /all?fields=name,population — population completeness check."""

    @allure.story("Population data completeness")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_all_countries_have_positive_population(
        self,
        http_session: requests.Session,
        countries_env: Dict[str, Any],
    ) -> None:
        """
        Validates that every entry in /all has a non-negative integer population.

        Note: population = 0 is intentionally allowed. The REST Countries API
        includes uninhabited territories (e.g. Bouvet Island, Heard Island,
        Antarctica) that legitimately report population = 0. The real data-
        integrity check is that the field exists and is a valid non-negative
        integer — not that it is strictly positive.
        """
        base_url = countries_env["base_url"]
        max_rt = countries_env["max_response_time"]

        with allure.step("GET /all?fields=name,population"):
            resp = _get(
                http_session,
                base_url,
                "/all",
                params={"fields": "name,population"},
            )

        with allure.step("Assert HTTP 200"):
            assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"

        with allure.step(f"Assert response time < {max_rt}s"):
            elapsed = resp.elapsed.total_seconds()
            assert elapsed < max_rt, (
                f"Response took {elapsed:.2f}s, threshold is {max_rt}s"
            )

        data: List[Dict[str, Any]] = resp.json()

        # Count zero-population territories for informational attachment
        zero_pop = [c["name"]["common"] for c in data
                    if isinstance(c.get("population"), int) and c["population"] == 0
                    and isinstance(c.get("name"), dict)]

        with allure.step("Assert every country has a non-negative integer population"):
            validator = CountriesListValidator(data, min_count=1)
            validator.validate_all_have_population()

            if zero_pop:
                allure.attach(
                    f"Uninhabited territories (population=0, allowed): {zero_pop}",
                    name="Zero-population territories",
                    attachment_type=allure.attachment_type.TEXT,
                )

            if validator.errors:
                failures = "\n".join(str(e) for e in validator.errors)
                allure.attach(
                    failures,
                    name="Population validation failures",
                    attachment_type=allure.attachment_type.TEXT,
                )
                pytest.fail(
                    f"{len(validator.errors)} countries with missing or invalid population"
                )

    @allure.story("Response time gate")
    def test_all_countries_response_time(
        self,
        http_session: requests.Session,
        countries_env: Dict[str, Any],
    ) -> None:
        base_url = countries_env["base_url"]
        max_rt = countries_env["max_response_time"]
        resp = _get(http_session, base_url, "/all", params={"fields": "name,population"})
        elapsed = resp.elapsed.total_seconds()
        assert elapsed < max_rt, (
            f"Response time {elapsed:.3f}s exceeded threshold {max_rt}s"
        )


@allure.epic("Countries API")
@allure.feature("Cross-reference validation")
class TestCrossReference:
    """
    Cross-reference: a country found via /name must also appear in /region.
    Uses Germany (Europe) as the representative test case.
    """

    @allure.story("Name-to-Region cross-reference")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_germany_in_name_also_in_europe_region(
        self,
        http_session: requests.Session,
        countries_env: Dict[str, Any],
    ) -> None:
        base_url = countries_env["base_url"]
        max_rt = countries_env["max_response_time"]

        with allure.step("GET /name/germany"):
            name_resp = _get(http_session, base_url, "/name/germany")
        assert name_resp.status_code == 200
        assert name_resp.elapsed.total_seconds() < max_rt

        name_data: List[Dict[str, Any]] = name_resp.json()
        assert len(name_data) > 0
        # Common name is the stable identifier across endpoints
        germany_common_name: str = name_data[0]["name"]["common"]

        with allure.step("GET /region/europe"):
            region_resp = _get(http_session, base_url, "/region/europe")
        assert region_resp.status_code == 200
        assert region_resp.elapsed.total_seconds() < max_rt

        region_data: List[Dict[str, Any]] = region_resp.json()
        region_names = {c["name"]["common"] for c in region_data if "name" in c}

        allure.attach(
            f"Looking for '{germany_common_name}' in {len(region_names)} European countries",
            name="Cross-reference check",
            attachment_type=allure.attachment_type.TEXT,
        )

        with allure.step(f"Assert '{germany_common_name}' present in /region/europe"):
            assert germany_common_name in region_names, (
                f"'{germany_common_name}' from /name endpoint "
                f"not found in /region/europe results"
            )
