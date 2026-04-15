# Skill: Test Generator

Given an endpoint URL, HTTP method, and response field list, generate a complete
pytest test file with fixtures, parametrize, markers, and both positive and negative tests.

---

## Input Format

Provide the following to Claude:

```
Endpoint: GET https://restcountries.com/v3.1/region/{region}
Response fields: name (object), capital (list), population (int), area (float), flag (str)
Environment fixture: countries_env
```

---

## Output Requirements

Claude must generate a file that:

1. **Imports** follow the framework import order (stdlib → third-party → local).
2. **pytestmark** is set at module level with the correct marker.
3. **Allure decorators** (`@allure.epic`, `@allure.feature`, `@allure.story`,
   `@allure.severity`) are present on every class and function.
4. **Positive tests** cover:
   - HTTP 200 response
   - Response time < `env_cfg["max_response_time"]` (from fixture, never hardcoded)
   - Schema validation via a `BaseValidator` subclass in `src/validators/`
   - Data completeness (non-empty lists, positive integers, etc.)
5. **Negative tests** cover:
   - Invalid path parameter (e.g. non-existent region name) → expect 404 or 400
   - Missing required query parameter (if applicable) → expect 400 or 422
6. **Parametrize** from JSON if the endpoint is city/country/entity-based.
7. All thresholds come from the environment fixture — zero hardcoded values.
8. `allure.attach()` is called on validation failures to surface data in the report.

---

## Template

```python
"""
<Subject> API test suite.

Targets: <base_url>/<path>
Environment config injected via `<env>_env` fixture.
"""
from __future__ import annotations
from typing import Any, Dict
import allure
import pytest
import requests
from src.validators.<subject>_validator import <Subject>Validator

pytestmark = [pytest.mark.<env>]


@allure.epic("<API Name>")
@allure.feature("<Feature>")
class Test<Subject>:

    @allure.story("HTTP 200 and schema")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_<endpoint>_returns_200_and_valid_schema(
        self,
        http_session: requests.Session,
        <env>_env: Dict[str, Any],
    ) -> None:
        base_url = <env>_env["base_url"]
        max_rt = <env>_env["max_response_time"]

        with allure.step("GET <path>"):
            resp = http_session.get(f"{base_url}/<path>", timeout=10)

        with allure.step("Assert HTTP 200"):
            assert resp.status_code == 200

        with allure.step(f"Assert response time < {max_rt}s"):
            assert resp.elapsed.total_seconds() < max_rt

        data = resp.json()
        with allure.step("Validate schema"):
            validator = <Subject>Validator(data[0] if isinstance(data, list) else data)
            validator.assert_valid()

    @allure.story("Negative — invalid parameter")
    @allure.severity(allure.severity_level.NORMAL)
    def test_<endpoint>_invalid_param_returns_404(
        self,
        http_session: requests.Session,
        <env>_env: Dict[str, Any],
    ) -> None:
        base_url = <env>_env["base_url"]
        resp = http_session.get(f"{base_url}/<path>/INVALID_VALUE_XYZ", timeout=10)
        assert resp.status_code in (404, 400), (
            f"Expected 404 or 400 for invalid param, got {resp.status_code}"
        )
```

---

## Validator Generation

When generating the test file, also generate the corresponding validator (see
`validator-generator.md`) and place it in `src/validators/<subject>_validator.py`.
