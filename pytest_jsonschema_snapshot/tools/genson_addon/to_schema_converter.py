"""Json → Schema with optional format handling.

`format_mode` options
---------------------
* ``"on"``   – detect formats and let validators assert them (default).
* ``"off"``  – ignore formats entirely.
* ``"safe"`` – keep the annotations but embed a ``$vocabulary`` block that
                **disables** the draft‑2020‑12 *format‑assertion* vocabulary.
                This makes every ``format`` purely informational, regardless
                of validator settings.
"""

from typing import Any, Dict, Literal

from genson import SchemaBuilder  # type: ignore[import-untyped]

from .format_detector import FormatDetector

_FormatMode = Literal["on", "off", "safe"]


class JsonToSchemaConverter(SchemaBuilder):
    """A thin wrapper around :class:`genson.SchemaBuilder`."""

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------
    def __init__(
        self,
        schema_uri: str = "https://json-schema.org/draft/2020-12/schema",
        *,
        format_mode: _FormatMode = "on",
    ):
        super().__init__(schema_uri) if schema_uri else super().__init__()
        if format_mode not in {"on", "off", "safe"}:
            raise ValueError("format_mode must be 'on', 'off', or 'safe'.")
        self._format_mode: _FormatMode = format_mode
        self._format_cache: Dict[str, set[str]] = {}

    # ------------------------------------------------------------------
    # Public API (overrides)
    # ------------------------------------------------------------------
    def add_object(self, obj: Any, path: str = "root") -> None:
        super().add_object(obj)
        if self._format_mode != "off":
            self._collect_formats(obj, path)

    def to_schema(self) -> Dict[str, Any]:
        schema = dict(super().to_schema())  # shallow‑copy

        if self._format_mode != "off":
            self._inject_formats(schema, "root")

            if self._format_mode == "safe":
                schema.setdefault(
                    "$vocabulary",
                    {
                        "https://json-schema.org/draft/2020-12/vocab/core": True,
                        "https://json-schema.org/draft/2020-12/vocab/applicator": True,
                        "https://json-schema.org/draft/2020-12/vocab/format-annotation": True,
                        "https://json-schema.org/draft/2020-12/vocab/format-assertion": False,
                    },
                )

        return schema

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------
    def _collect_formats(self, obj: Any, path: str) -> None:
        if isinstance(obj, str):
            fmt = FormatDetector.detect_format(obj)
            if fmt:
                self._format_cache.setdefault(path, set()).add(fmt)
        elif isinstance(obj, dict):
            for k, v in obj.items():
                self._collect_formats(v, f"{path}.{k}")
        elif isinstance(obj, (list, tuple)):
            for i, item in enumerate(obj):
                self._collect_formats(item, f"{path}[{i}]")

    def _inject_formats(self, schema: Dict[str, Any], path: str) -> None:
        t = schema.get("type")
        if t == "string":
            fmts = self._format_cache.get(path)
            if fmts and len(fmts) == 1:
                schema["format"] = next(iter(fmts))
        elif t == "object" and "properties" in schema:
            for name, subschema in schema["properties"].items():
                self._inject_formats(subschema, f"{path}.{name}")
        elif t == "array" and "items" in schema:
            items_schema = schema["items"]
            if isinstance(items_schema, dict):
                self._inject_formats(items_schema, f"{path}[0]")
            else:
                for idx, subschema in enumerate(items_schema):
                    self._inject_formats(subschema, f"{path}[{idx}]")
        elif "anyOf" in schema:
            for subschema in schema["anyOf"]:
                self._inject_formats(subschema, path)
