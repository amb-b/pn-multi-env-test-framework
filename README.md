API test framework demonstrating environment abstraction, YAML-driven
configuration, typed validators, Allure reporting, and a full CI pipeline.

**APIs under test:**
- REST Countries — `https://restcountries.com/v3.1`
- Open-Meteo Weather — `https://api.open-meteo.com/v1`

---

## Project Structure

```
panw-qa-assignment/
├── config/
│   └── environments.yaml       # All base URLs and thresholds — zero hardcoding in tests
├── test_data/
│   └── cities.json             # Parametrize source for weather tests (5 cities)
├── src/
│   └── validators/
│       ├── base_validator.py   # Abstract base — all validators extend this
│       ├── countries_validator.py
│       └── weather_validator.py
├── tests/
│   ├── test_countries.py       # Region, name search, all-countries, cross-reference
│   └── test_weather.py         # Forecast: 200, timing, temp range, hourly count, timezone
├── conftest.py                 # --env CLI flag, fixtures, Allure environment writer
├── .github/workflows/ci.yml    # 3-job pipeline: countries | weather | combined + quality gate
├── .claude/
│   ├── rules/                  # testing-standards, code-style, framework-rules
│   └── skills/                 # test-generator, validator-generator prompts
├── CLAUDE_LOG.md               # Parallel agent log, decisions, edge cases
├── requirements.txt
└── pytest.ini
```

---

## Setup

### Prerequisites
- Python 3.11+
- (Optional) Java 11+ for generating the Allure HTML report locally

### Install dependencies

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### (Optional) Install Allure CLI

```bash
# macOS
brew install allure

# Linux — see https://allurereport.org/docs/install/
```

---

## Running Tests Locally

### Run both environments (default)

```bash
pytest
```

### Run only the Countries API tests

```bash
pytest --env countries
```

### Run only the Weather API tests

```bash
pytest --env weather
```

### Run with Allure results collection

```bash
pytest --alluredir=allure-results
allure serve allure-results      # opens report in browser
```

### Run with HTML report (no Allure CLI needed)

```bash
pytest --html=reports/report.html --self-contained-html
```

---

## Interpreting Test Results

### Console output

Each test prints a structured line:
```
PASSED tests/test_countries.py::TestRegionEurope::test_europe_returns_more_than_40_countries
PASSED tests/test_weather.py::test_forecast_returns_200[New_York]
```

Failures show a short traceback (`--tb=short`) pointing directly to the assertion.

### Allure report

Open the generated report and navigate by **Epic → Feature → Story**:

| Epic | Feature | What it covers |
|---|---|---|
| Countries API | Region endpoint | `/region/europe` result count, response time |
| Countries API | Name search | `/name/germany` schema validation |
| Countries API | All countries | `/all` population completeness |
| Countries API | Cross-reference | name ↔ region consistency |
| Weather API | Forecast endpoint | 200 status, response time, temp range, hourly count, timezone |

Each failed test includes an Allure attachment with the specific validation errors.

### Quality gate

The CI `test-all-and-quality-gate` job runs a Python script that parses the JUnit XML
and exits 1 if any test failed. The pipeline step shows:

```
QUALITY GATE REPORT
==================================================
  Total Tests : 29
  Passed      : 29
  Failed      : 0
  Errors      : 0
  Skipped     : 0
==================================================
QUALITY GATE PASSED: All tests green
```

---

## Design Decisions

### 1. YAML-driven configuration
All base URLs, response time thresholds, result count minimums, and temperature ranges
live in `config/environments.yaml`. Test files receive these values through pytest
fixtures — no numeric literals appear in test code. Adding a new environment requires
only a YAML change and a new fixture.

### 2. Typed validator hierarchy
A `BaseValidator` in `src/validators/` provides reusable field-checking primitives.
All concrete validators (`CountriesValidator`, `WeatherForecastValidator`) extend it.
This separates validation logic from test orchestration and makes validators testable
in isolation.

### 3. Module-level parametrize for weather cities
`test_weather.py` loads `cities.json` at **collection time** via a module-level
`_city_params()` call. This ensures pytest generates human-readable test IDs
(e.g. `[New_York]`, `[London]`) without requiring `pytest-lazy-fixture`.

### 4. Session-scoped HTTP client
A single `requests.Session` is shared across all tests in a run, enabling TCP
connection reuse while still allowing per-test response time assertions.

### 5. Three-job CI pipeline
Countries and weather jobs run **in parallel**, then a combined job runs the full
suite and enforces the quality gate. This gives fast per-environment feedback without
sacrificing an end-to-end correctness check.

---

## Assumptions

- Both APIs are publicly accessible (no auth, no rate limiting under normal test load).
- Open-Meteo may return `null` entries in `temperature_2m` for distant forecast hours;
  these are treated as missing data (not failures).
- The `population: 0` constraint from the assignment is applied strictly — territories
  with 0 population are flagged as failures, matching the spec wording.
- Allure CLI is available in CI; the pipeline installs it from the official release tarball.
