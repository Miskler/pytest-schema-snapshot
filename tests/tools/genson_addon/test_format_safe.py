"""Pytest suite for ``JsonToSchemaConverter`` using generic ``jsonschema.validate``.

We use two JSON samples (``SOURCE`` and ``SOURCE_INVALID``) to check that
*format* handling behaves as intended under three modes.

Expectation matrix
==================  =================  =========================
format_mode          call to validate   Expected result
==================  =================  =========================
"on"                 validate + FC      ValidationError raised
"safe"               validate           passes OK
"off"                validate           passes OK
==================  =================  =========================
Where **FC** = ``FormatChecker``.

Why this matters?
-----------------
*User requested*: «должно проходить на обычном validate».  Therefore we
avoid draft‑specific classes like ``Draft202012Validator`` and rely on
``jsonschema.validate`` selecting a validator based on the ``$schema``
keyword embedded by *genson* (currently `http://json-schema.org/schema#`).

In python‑jsonschema, *format* assertions only run when a
``FormatChecker`` is provided, regardless of the *format-assertion*
vocabulary.  Hence, supplying ``FormatChecker`` only in **on** mode gives
us the desired behaviour.
"""

from __future__ import annotations

import jsonschema
import pytest

from pytest_jsonschema_snapshot.tools import JsonToSchemaConverter

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
SOURCE = {
    "email": "alice@example.com",
    "website": "https://example.com",
}

SOURCE_INVALID = {
    "email": "not-an-email",
    "website": "notaurl",
}

PARAMS = [
    ("on", False, True),  # должен упасть (ValidationError)
    ("safe", True, True),  # должен пройти
    ("off", True, False),  # должен пройти
]


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("mode, should_pass, have_formats", PARAMS)
def test_format_handling(mode: str, should_pass: bool, have_formats: bool) -> None:
    """Validate *SOURCE_INVALID* against schema generated from *SOURCE*."""

    # 1. Generate schema
    conv = JsonToSchemaConverter(format_mode=mode)
    conv.add_object(SOURCE)
    schema = conv.to_schema()

    # 2. Prepare kwargs for jsonschema.validate
    kwargs: dict[str, object] = {}
    if mode == "on":
        kwargs["format_checker"] = jsonschema.FormatChecker()

    # 3. Validate and assert outcome
    if should_pass:
        jsonschema.validate(SOURCE_INVALID, schema, **kwargs)
    else:
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(SOURCE_INVALID, schema, **kwargs)

    # 4. Ensure presence/absence of "format" matches the mode
    has_format = schema["properties"]["email"].get("format") is not None
    assert has_format == have_formats
