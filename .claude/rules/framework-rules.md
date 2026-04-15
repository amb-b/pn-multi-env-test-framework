# Framework Architecture Rules — PANW QA Framework

These rules define the structural constraints of this test framework. They exist to
maintain consistency, testability, and extensibility as the framework scales.

---

## Directory Layout

```
panw-qa-assignment/
├── config/            # YAML environment configs ONLY — no Python here
├── test_data/         # Static JSON fixture data ONLY — no Python here
├── src/
│   └── validators/    # All validator classes (extend BaseValidator)
├── tests/             # All pytest test files
├── conftest.py        # Top-level: CLI flag, session fixtures, Allure config
├── .claude/
│   ├── rules/         # Framework rules (this directory)
│   └── skills/        # Code-generation prompts for Claude
├── .github/workflows/ # CI pipeline definitions
└── requirements.txt   # Pinned dependencies
```

**Rule:** Every file must live in its designated directory. No exceptions.

---

## Configuration

- **All runtime configuration lives in `config/environments.yaml`.**
- `base_url`, `max_response_time`, `min_results_count`, `temperature_range` — all from YAML.
- Test files read config exclusively through fixtures (`countries_env`, `weather_env`).
- **Never hardcode URLs, timeouts, or numeric thresholds** anywhere in `tests/` or `src/`.

---

## Environment Abstraction

- The `--env` CLI flag is implemented via `pytest_addoption` in the top-level `conftest.py`.
- `countries_env` and `weather_env` fixtures handle skip logic automatically.
- Adding a new environment requires only:
  1. A new entry in `config/environments.yaml`
  2. A new fixture in `conftest.py`
  3. New test files using that fixture
  No changes to existing tests.

---

## Validator Architecture

- All validators must extend `BaseValidator` from `src/validators/base_validator.py`.
- `BaseValidator` provides shared primitives: `_require_field`, `_require_type`,
  `_require_in_range`, `_require_positive`, etc.
- **Validators must not make HTTP calls.** They only validate data passed to them.
- Validators collect errors rather than raising immediately (fail-all pattern) so
  Allure attachments can capture the full error list.
- `assert_valid()` is the entry point for tests that want fail-fast behaviour.

---

## Test File Isolation

- **Test files must not import from other test files.**
  - Shared helpers go in `conftest.py` or `src/`.
  - This ensures each test module can be collected and run independently.
- Each test file declares its own `pytestmark` for marker-based selection.

---

## Fixture Scoping

- `scope="session"` — HTTP client, environment configs, cities data.
- `scope="function"` — any state that must not leak between tests.
- Never use `scope="module"` (it creates implicit test ordering dependencies).

---

## Data Files

- `test_data/cities.json` is the **single source of truth** for city data.
- Parametrized tests load this file at **collection time** (module-level `_city_params()`),
  so pytest can generate meaningful test IDs without fixture execution.
- Adding a city = editing the JSON only. No Python changes required.

---

## CI Pipeline

- Pipeline **must fail** if any test fails or if the quality gate script exits non-zero.
- Countries and weather jobs run in parallel; the combined job runs after both complete.
- Allure reports are uploaded as artifacts with a 30-day retention policy.
- The quality gate script (`python - <<'EOF' ... EOF`) prints a structured summary
  and exits with code 1 on any failure.

---

## Extensibility Checklist

When adding a new API/environment to the framework:

- [ ] Add entry to `config/environments.yaml`
- [ ] Add a new fixture in `conftest.py` with skip logic
- [ ] Create `src/validators/<name>_validator.py` extending `BaseValidator`
- [ ] Create `tests/test_<name>.py` with `pytestmark = [pytest.mark.<name>]`
- [ ] Add `<name>` to `choices` in `pytest_addoption`
- [ ] Add a new job in `.github/workflows/ci.yml`
- [ ] Update `README.md`

No existing files should need modification.
