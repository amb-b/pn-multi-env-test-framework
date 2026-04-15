# Skill: Validator Generator

Given a sample JSON response body, generate a typed validator class that extends
`BaseValidator` with per-field type checks and required field validation.

---

## Input Format

Provide Claude with a sample JSON response:

```json
{
  "name": { "common": "Germany", "official": "Federal Republic of Germany" },
  "capital": ["Berlin"],
  "population": 83240525,
  "currencies": { "EUR": { "name": "Euro", "symbol": "€" } },
  "languages": { "deu": "German" },
  "area": 357114.0,
  "flag": "🇩🇪"
}
```

---

## Output Requirements

Claude must generate a validator that:

1. **Extends `BaseValidator`** from `src/validators/base_validator.py`.
2. **Uses only the protected helpers** (`_require_field`, `_require_type`,
   `_require_non_empty`, `_require_positive`, `_require_in_range`) — no bare assertions.
3. **Has a private `_validate_<field>` method for every field** in the sample JSON.
4. **`validate()` calls `super().validate()` first**, then each field validator.
5. **Type annotations** on every method parameter and return value.
6. **Collects all errors** rather than short-circuiting on the first failure.
7. **`assert_valid()`** raises `ValidationError` on the first collected error.

---

## Template

```python
"""
Typed validator for <API Name> <endpoint> responses.
Generated from the <path> sample response schema.
"""
from __future__ import annotations
from typing import Any, Dict, List
from .base_validator import BaseValidator, ValidationError


class <Subject>Validator(BaseValidator):
    """
    Validates a single <subject> object from the <API Name> API.

    Required fields: <comma-separated field list>
    """

    REQUIRED_FIELDS: List[str] = [<"field1", "field2", ...>]

    def __init__(self, data: Dict[str, Any]) -> None:
        super().__init__(data)

    def validate(self) -> "<Subject>Validator":
        super().validate()
        self._validate_<field1>()
        self._validate_<field2>()
        # ... one method per field
        return self

    def _validate_<field1>(self) -> None:
        value = self._require_field(self._data, "<field1>")
        if value is None:
            return
        self._require_type("<field1>", value, <expected_type>)
        # additional checks: _require_non_empty, _require_positive, etc.

    def _validate_<field2>(self) -> None:
        value = self._require_field(self._data, "<field2>")
        if value is None:
            return
        self._require_type("<field2>", value, <expected_type>)
```

---

## Type Mapping

| JSON type | Python type |
|---|---|
| string | `str` |
| integer | `int` |
| float / number | `float` |
| boolean | `bool` |
| object / dict | `dict` |
| array / list | `list` |
| null | handled by `_require_field` returning `None` |

---

## Post-Generation Checklist

- [ ] File saved to `src/validators/<subject>_validator.py`
- [ ] Class imported in `src/validators/__init__.py`
- [ ] Corresponding test in `tests/test_<subject>.py` uses `<Subject>Validator`
- [ ] No inline assertions in test files that duplicate validator logic
