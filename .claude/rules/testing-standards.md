# Testing Standards — PANW QA Framework

## Core Principles

These rules govern how tests are written in this framework. They apply to all files
under `tests/` and take precedence over generic Python testing conventions.

---

## Parametrization

- **Always parametrize from JSON data files**, never inline test data.
  - City test data lives exclusively in `test_data/cities.json`.
  - Adding a new city requires only a JSON edit — no Python changes.
  - Parametrize IDs must be human-readable (use `city["name"]`, not index integers).

```python
# CORRECT
@pytest.mark.parametrize("city", _CITIES, ids=[c["name"] for c in _CITIES])
def test_forecast_timezone_field_present(city, ...): ...

# WRONG — inline data
@pytest.mark.parametrize("lat,lon", [(40.71, -74.0), (51.5, -0.12)])
def test_forecast_timezone_field_present(lat, lon, ...): ...
```

---

## Schema Validation

- **Every endpoint must have at least one schema validation test.**
  - Schema checks live in `src/validators/`, never inline in test files.
  - Tests call `validator.assert_valid()` or check `validator.errors`.

```python
# CORRECT
validator = CountriesValidator(country)
validator.assert_valid()

# WRONG — inline assertion
assert "name" in country and "capital" in country
```

---

## Threshold Values

- **Zero threshold values may be hardcoded in test files.**
  - `max_response_time`, `min_results_count`, `temperature_range` come from the
    `environment_config` fixture which reads `config/environments.yaml`.
  - Tests access thresholds via `env_cfg["max_response_time"]`, never literals.

```python
# CORRECT
max_rt = weather_env["max_response_time"]
assert resp.elapsed.total_seconds() < max_rt

# WRONG
assert resp.elapsed.total_seconds() < 3.0
```

---

## Test Markers

- Every test file must declare `pytestmark` at module level:
  - `pytest.mark.countries` for all files in the countries suite.
  - `pytest.mark.weather` for all files in the weather suite.
- Markers enable `pytest -m countries` or `pytest -m weather` selection.

---

## Allure Annotations

- Every test class must have `@allure.epic`, `@allure.feature`.
- Every test function must have `@allure.story` and `@allure.severity`.
- Use `allure.dynamic.parameter(name, value)` for parametrized values.
- Attach response metadata on failure using `allure.attach()`.

---

## Fixture Rules

- Session fixtures (`scope="session"`) must be defined in the top-level `conftest.py`.
- Test-level fixtures belong in the same `conftest.py` or a `tests/conftest.py`.
- **Test files must not import from other test files** (see `framework-rules.md`).

---

## Negative / Edge Case Coverage

- Every endpoint test file must include at least one negative test or edge case.
- Negative tests should use `pytest.mark.xfail` only for known upstream bugs,
  never to suppress legitimate failures.
