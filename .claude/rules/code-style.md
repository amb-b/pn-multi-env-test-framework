# Code Style Rules — PANW QA Framework

These rules apply to all Python files in this project. They complement PEP 8 with
framework-specific conventions.

---

## Type Hints

- **All public functions and methods must have type hints** (parameters + return type).
- Use `from __future__ import annotations` at the top of every module to enable
  postponed evaluation and avoid circular import issues.
- Use `Optional[T]` rather than `T | None` for Python 3.9 compatibility.

```python
# CORRECT
def _require_field(self, obj: Dict[str, Any], field: str) -> Any: ...

# WRONG
def _require_field(self, obj, field): ...
```

---

## Validators

- **All validators live in `src/validators/`**, never inline in test files.
- Every validator class must extend `BaseValidator` from `src/validators/base_validator.py`.
- Validator `validate()` methods must call `super().validate()` first.
- Use the protected helper methods (`_require_field`, `_require_type`, etc.) instead
  of writing bare `assert` or `if` statements inside validators.
- Validators collect all errors (do not short-circuit) unless `assert_valid()` is called.

---

## Assertions

- **Never write bare `assert field in data` in test files** — delegate to a Validator.
- `assert` is permitted in tests only for:
  - HTTP status codes: `assert resp.status_code == 200`
  - Simple scalar checks after validator has confirmed field presence
  - Validator error reporting: `if validator.errors: pytest.fail(...)`

---

## Imports

- Import order (enforced by `isort` in CI):
  1. Standard library
  2. Third-party (`allure`, `pytest`, `requests`, `yaml`)
  3. Local (`from src.validators...`)
- No wildcard imports (`from module import *`).
- No cross-test-file imports (`from tests.test_countries import ...`).

---

## Naming

| Entity | Convention | Example |
|---|---|---|
| Test files | `test_<subject>.py` | `test_countries.py` |
| Test classes | `Test<Subject>` | `TestRegionEurope` |
| Test functions | `test_<what>_<condition>` | `test_germany_schema_has_required_fields` |
| Validator classes | `<Subject>Validator` | `CountriesValidator` |
| Private helpers | `_<verb>_<noun>` | `_get_forecast` |
| Constants | `UPPER_SNAKE_CASE` | `MIN_EUROPE_COUNTRIES` |

---

## Docstrings

- Module-level docstrings are required in all non-`__init__.py` files.
- Class docstrings explain what the class validates / tests.
- Function docstrings are required for all public functions; a single sentence is fine.

---

## Logging & Print

- Do not use `print()` in test or validator code.
- Use `allure.attach()` to surface debug information in the Allure report.
- Use Python's `logging` module only in framework utilities (not in tests).

---

## Line Length & Formatting

- Maximum line length: **100 characters** (configured in `pytest.ini` / `pyproject.toml`).
- String formatting: use f-strings exclusively (no `%` or `.format()`).
- Trailing commas required in multi-line function calls and data structures.
