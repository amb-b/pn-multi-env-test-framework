"""
Typed validator for REST Countries API responses.
Generated from the /name/germany sample response schema.
"""
from __future__ import annotations

from typing import Any, Dict, List

from .base_validator import BaseValidator, ValidationError


class CountriesValidator(BaseValidator):
    """
    Validates a single country object returned by the REST Countries API.

    Required fields (per assignment spec):
        name, capital, population, currencies, languages
    """

    REQUIRED_FIELDS: List[str] = [
        "name",
        "capital",
        "population",
        "currencies",
        "languages",
    ]

    def __init__(self, data: Dict[str, Any]) -> None:
        super().__init__(data)

    def validate(self) -> "CountriesValidator":
        super().validate()
        self._validate_name()
        self._validate_capital()
        self._validate_population()
        self._validate_currencies()
        self._validate_languages()
        return self

    # ------------------------------------------------------------------
    # Per-field validators
    # ------------------------------------------------------------------

    def _validate_name(self) -> None:
        name = self._require_field(self._data, "name")
        if name is None:
            return
        self._require_type("name", name, dict)
        if isinstance(name, dict):
            self._require_field(name, "common")
            self._require_field(name, "official")

    def _validate_capital(self) -> None:
        capital = self._require_field(self._data, "capital")
        if capital is None:
            return
        self._require_type("capital", capital, list)
        if isinstance(capital, list):
            self._require_non_empty("capital", capital)

    def _validate_population(self) -> None:
        population = self._require_field(self._data, "population")
        if population is None:
            return
        self._require_type("population", population, int)
        self._require_positive("population", population)

    def _validate_currencies(self) -> None:
        currencies = self._require_field(self._data, "currencies")
        if currencies is None:
            return
        self._require_type("currencies", currencies, dict)
        if isinstance(currencies, dict):
            self._require_non_empty("currencies", currencies)

    def _validate_languages(self) -> None:
        languages = self._require_field(self._data, "languages")
        if languages is None:
            return
        self._require_type("languages", languages, dict)
        if isinstance(languages, dict):
            self._require_non_empty("languages", languages)


class CountriesListValidator(BaseValidator):
    """Validates a list of country objects, e.g. from /region or /all."""

    def __init__(
        self,
        data: List[Dict[str, Any]],
        min_count: int = 1,
    ) -> None:
        super().__init__(data)
        self._min_count = min_count

    def validate(self) -> "CountriesListValidator":
        super().validate()
        self._require_type("response", self._data, list)
        if isinstance(self._data, list):
            self._require_min_length("results", self._data, self._min_count)
        return self

    def validate_all_have_population(self) -> "CountriesListValidator":
        """
        Assert every country entry has a population field that is a non-negative
        integer. Zero is permitted — some entries in the API are uninhabited
        territories (e.g. Bouvet Island, Antarctica) which legitimately report
        population = 0. The check guards against missing or non-numeric values.
        """
        if not isinstance(self._data, list):
            return self
        for idx, country in enumerate(self._data):
            pop = country.get("population")
            if pop is None or not isinstance(pop, int) or pop < 0:
                err = ValidationError(
                    f"results[{idx}].population",
                    "population must be a non-negative integer",
                    pop,
                )
                self._errors.append(err)
        return self
