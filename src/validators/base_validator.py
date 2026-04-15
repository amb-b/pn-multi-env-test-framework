"""
Base validator providing common validation primitives for all API validators.
All validators in this framework must extend BaseValidator.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Type


class ValidationError(Exception):
    """Raised when a validation check fails."""

    def __init__(self, field: str, message: str, value: Any = None) -> None:
        self.field = field
        self.message = message
        self.value = value
        super().__init__(f"[{field}] {message} (got: {value!r})")


class BaseValidator:
    """
    Abstract base for all schema/response validators.

    Subclasses implement `validate(data)` and call the helper methods here
    rather than writing inline assertions in test files.
    """

    def __init__(self, data: Any) -> None:
        self._data = data
        self._errors: List[ValidationError] = []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def validate(self) -> "BaseValidator":
        """
        Run all validations.  Subclasses must override and call super().validate().
        Raises ValidationError on the first failure when used via assert_valid().
        """
        return self

    def assert_valid(self) -> None:
        """Re-raises the first collected error, if any."""
        self.validate()
        if self._errors:
            raise self._errors[0]

    @property
    def errors(self) -> List[ValidationError]:
        return list(self._errors)

    # ------------------------------------------------------------------
    # Protected helpers — use these inside validate(), never in test files
    # ------------------------------------------------------------------

    def _require_field(self, obj: Dict[str, Any], field: str) -> Any:
        """Assert field is present and not None; record error otherwise."""
        if not isinstance(obj, dict):
            err = ValidationError(field, "parent object is not a dict", type(obj))
            self._errors.append(err)
            return None
        if field not in obj or obj[field] is None:
            err = ValidationError(field, "required field missing or null")
            self._errors.append(err)
            return None
        return obj[field]

    def _require_type(self, field: str, value: Any, expected: Type) -> bool:
        """Assert value is an instance of expected type."""
        if not isinstance(value, expected):
            err = ValidationError(
                field,
                f"expected type {expected.__name__}",
                type(value).__name__,
            )
            self._errors.append(err)
            return False
        return True

    def _require_non_empty(self, field: str, value: Any) -> bool:
        """Assert list/dict/string is non-empty."""
        if not value:
            err = ValidationError(field, "value must be non-empty", value)
            self._errors.append(err)
            return False
        return True

    def _require_min_length(self, field: str, value: List, minimum: int) -> bool:
        """Assert list has at least `minimum` elements."""
        if len(value) < minimum:
            err = ValidationError(
                field, f"expected at least {minimum} items", len(value)
            )
            self._errors.append(err)
            return False
        return True

    def _require_in_range(
        self,
        field: str,
        value: float,
        low: float,
        high: float,
    ) -> bool:
        """Assert numeric value is within [low, high] inclusive."""
        if not (low <= value <= high):
            err = ValidationError(
                field, f"value must be between {low} and {high}", value
            )
            self._errors.append(err)
            return False
        return True

    def _require_positive(self, field: str, value: Any) -> bool:
        """Assert numeric value is strictly positive."""
        if not isinstance(value, (int, float)) or value <= 0:
            err = ValidationError(field, "value must be > 0", value)
            self._errors.append(err)
            return False
        return True
