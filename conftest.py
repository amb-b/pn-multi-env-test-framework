"""
Top-level conftest.py — environment fixture and CLI flag implementation.

The --env flag selects which environment(s) to test:
  --env countries   → run only countries tests
  --env weather     → run only weather tests
  (no flag)         → run both environments

All environment configuration (base_url, thresholds) is read from
config/environments.yaml.  Zero values are hardcoded in test files.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Generator, Optional

import allure
import pytest
import requests
import yaml

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
ROOT_DIR = Path(__file__).parent
CONFIG_PATH = ROOT_DIR / "config" / "environments.yaml"
CITIES_PATH = ROOT_DIR / "test_data" / "cities.json"


# ---------------------------------------------------------------------------
# CLI option
# ---------------------------------------------------------------------------

def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--env",
        action="store",
        default=None,
        choices=["countries", "weather"],
        help=(
            "Select the target environment.  "
            "Omit to run both.  "
            "Choices: countries | weather"
        ),
    )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _load_config() -> Dict[str, Any]:
    """Load and return the full environments YAML as a dict."""
    with CONFIG_PATH.open() as fh:
        return yaml.safe_load(fh)


def _get_env_config(name: str) -> Dict[str, Any]:
    cfg = _load_config()
    envs = cfg.get("environments", {})
    if name not in envs:
        raise KeyError(
            f"Environment '{name}' not found in {CONFIG_PATH}. "
            f"Available: {list(envs.keys())}"
        )
    return envs[name]


# ---------------------------------------------------------------------------
# Session-scoped HTTP client
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def http_session() -> Generator[requests.Session, None, None]:
    """Shared requests.Session for all tests in the session."""
    session = requests.Session()
    session.headers.update({"Accept": "application/json"})
    yield session
    session.close()


# ---------------------------------------------------------------------------
# Environment fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def all_environments() -> Dict[str, Any]:
    """Return the full environments config dict."""
    return _load_config()["environments"]


@pytest.fixture(scope="session")
def countries_env(request: pytest.FixtureRequest) -> Dict[str, Any]:
    """
    Inject the 'countries' environment config into tests.
    Skips automatically when --env weather is provided.
    """
    env_flag: Optional[str] = request.config.getoption("--env")
    if env_flag is not None and env_flag != "countries":
        pytest.skip(f"Skipping countries suite: --env={env_flag}")
    return _get_env_config("countries")


@pytest.fixture(scope="session")
def weather_env(request: pytest.FixtureRequest) -> Dict[str, Any]:
    """
    Inject the 'weather' environment config into tests.
    Skips automatically when --env countries is provided.
    """
    env_flag: Optional[str] = request.config.getoption("--env")
    if env_flag is not None and env_flag != "weather":
        pytest.skip(f"Skipping weather suite: --env={env_flag}")
    return _get_env_config("weather")


# ---------------------------------------------------------------------------
# Data fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def cities() -> list:
    """Return the list of city dicts from test_data/cities.json."""
    with CITIES_PATH.open() as fh:
        return json.load(fh)


# ---------------------------------------------------------------------------
# Allure environment info helper
# ---------------------------------------------------------------------------

def pytest_configure(config: pytest.Config) -> None:
    """Write Allure environment.properties for per-environment labelling."""
    env_flag = config.getoption("--env", default=None)
    allure_dir = config.getoption("--alluredir", default=None)
    if allure_dir:
        props_path = Path(allure_dir) / "environment.properties"
        props_path.parent.mkdir(parents=True, exist_ok=True)
        cfg = _load_config()["environments"]
        lines = [f"Test.Environment={env_flag or 'all'}"]
        for env_name, env_cfg in cfg.items():
            if env_flag is None or env_flag == env_name:
                lines.append(f"{env_name}.base_url={env_cfg['base_url']}")
                lines.append(
                    f"{env_name}.max_response_time={env_cfg['max_response_time']}"
                )
        props_path.write_text("\n".join(lines) + "\n")
