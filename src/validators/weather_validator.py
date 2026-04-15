"""
Typed validator for Open-Meteo forecast API responses.
Generated from the /v1/forecast sample response schema.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from .base_validator import BaseValidator, ValidationError


class WeatherForecastValidator(BaseValidator):
    """
    Validates a single forecast response from the Open-Meteo API.

    Checks:
      - timezone field is present and non-empty
      - hourly.temperature_2m list is present and non-empty
      - all temperatures fall within the acceptable physical range (-80°C to 60°C)
    """

    TEMP_MIN: float = -80.0
    TEMP_MAX: float = 60.0

    def __init__(
        self,
        data: Dict[str, Any],
        temp_min: Optional[float] = None,
        temp_max: Optional[float] = None,
    ) -> None:
        super().__init__(data)
        self._temp_min = temp_min if temp_min is not None else self.TEMP_MIN
        self._temp_max = temp_max if temp_max is not None else self.TEMP_MAX

    def validate(self) -> "WeatherForecastValidator":
        super().validate()
        self._validate_timezone()
        self._validate_hourly()
        return self

    # ------------------------------------------------------------------
    # Per-field validators
    # ------------------------------------------------------------------

    def _validate_timezone(self) -> None:
        tz = self._require_field(self._data, "timezone")
        if tz is None:
            return
        self._require_type("timezone", tz, str)
        self._require_non_empty("timezone", tz)

    def _validate_hourly(self) -> None:
        hourly = self._require_field(self._data, "hourly")
        if hourly is None:
            return
        self._require_type("hourly", hourly, dict)
        if not isinstance(hourly, dict):
            return

        temps = self._require_field(hourly, "temperature_2m")
        if temps is None:
            return
        self._require_type("hourly.temperature_2m", temps, list)
        if not isinstance(temps, list):
            return

        self._require_non_empty("hourly.temperature_2m", temps)
        self._validate_temperature_range(temps)

    def _validate_temperature_range(self, temps: List[Any]) -> None:
        """Assert every temperature reading is within physical bounds."""
        for idx, temp in enumerate(temps):
            if temp is None:
                # Null readings are allowed (missing data marker)
                continue
            if not isinstance(temp, (int, float)):
                self._errors.append(
                    ValidationError(
                        f"hourly.temperature_2m[{idx}]",
                        "temperature must be numeric",
                        temp,
                    )
                )
                continue
            self._require_in_range(
                f"hourly.temperature_2m[{idx}]",
                float(temp),
                self._temp_min,
                self._temp_max,
            )

    def hourly_count(self) -> int:
        """Return the number of hourly temperature entries."""
        try:
            return len(self._data["hourly"]["temperature_2m"])
        except (KeyError, TypeError):
            return 0

    def timezone(self) -> Optional[str]:
        """Return the timezone string from the response."""
        return self._data.get("timezone")
