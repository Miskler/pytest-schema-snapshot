"""
Module for advanced JSON Schema generation with controllable `format` behavior
and automatic examples collection.
"""
from __future__ import annotations

from typing import Any, Dict, Optional, Literal, List, Tuple

from genson import SchemaBuilder  # type: ignore[import-untyped]

from .format_detector import FormatDetector


FormatMode = Literal["off", "on", "safe"]


class JsonToSchemaConverter(SchemaBuilder):
    @staticmethod
    def _is_primitive(value):
        return isinstance(value, (str, int, float, bool)) or value is None

    """
    Extended SchemaBuilder with format detection and examples support.

    Args:
        schema_uri: Optional explicit $schema value for the base builder.
        format: One of "off" | "on" | "safe".
            - "off": do not emit the `format` keyword at all.
            - "on":  detect and emit `format` normally (validation engines may enforce it).
            - "safe": emit `format`, but also set $vocabulary to disable format assertions
                      (keeps `format` as an annotation only).
        examples: Non-negative integer. If > 0, collects up to N distinct examples per path
                  and emits the `examples` keyword in the schema nodes.
    """

    def __init__(
        self,
        schema_uri: Optional[str] = None,
        *,
        format: FormatMode = "on",
        examples: int = 0,
    ) -> None:
        # Initialize base builder
        if schema_uri:
            super().__init__(schema_uri)
        else:
            super().__init__()

        # Runtime knobs
        if format not in ("off", "on", "safe"):
            raise ValueError("format must be one of: 'off', 'on', 'safe'")
        if examples < 0:
            raise ValueError("examples must be >= 0")

        self._format_mode: FormatMode = format
        self._examples_limit: int = int(examples)

        # Caches indexed by logical path (like "root.a[0].b")
        self._format_cache: Dict[str, set] = {}
        self._examples_cache: Dict[str, List[Any]] = {}

    # ------------------------- Public API -------------------------

    def add_object(self, obj: Any, path: str = "root") -> None:
        """
        Add an object into the builder and collect annotations for the same path tree.
        """
        # Build base structural schema first
        super().add_object(obj)
        # Then collect formats and examples along the same path mapping
        self._process(obj, path)

    def to_schema(self) -> Dict[str, Any]:
        """
        Generate the final schema, injecting `format` (according to the mode)
        and `examples` (if enabled).
        """
        schema = dict(super().to_schema())

        # If safe-mode is requested, ensure draft 2020-12 + disable format assertions.
        if self._format_mode == "safe":
            # Do not clobber an explicitly provided $schema if set by the user
            schema.setdefault("$schema", "https://json-schema.org/draft/2020-12/schema")
            schema["$vocabulary"] = {
                # Minimal, but include relevant vocabularies commonly understood by validators
                "https://json-schema.org/draft/2020-12/vocab/core": True,
                "https://json-schema.org/draft/2020-12/vocab/applicator": True,
                "https://json-schema.org/draft/2020-12/vocab/validation": True,
                "https://json-schema.org/draft/2020-12/vocab/meta-data": True,
                "https://json-schema.org/draft/2020-12/vocab/format-annotation": True,
                # Key point: keep formats as annotations only
                "https://json-schema.org/draft/2020-12/vocab/format-assertion": False,
            }

        # Inject formats/examples recursively
        self._inject_annotations(schema, "root")

        return schema

    # ----------------------- Internal helpers -----------------------

    def _process(self, obj: Any, path: str) -> None:
        """
        Recursively collect:
          - detected formats for strings (if mode != "off")
          - example values (if examples_limit > 0)
        """
        # Examples: record current value for this path (first, before descent)
        if self._examples_limit > 0:
            self._add_example(path, obj)

        # Formats: only for strings, only when enabled
        if isinstance(obj, str) and self._format_mode in ("on", "safe"):
            detected = FormatDetector.detect_format(obj)
            if detected:
                self._format_cache.setdefault(path, set()).add(detected)

        # Descend into structures
        if isinstance(obj, dict):
            for key, value in obj.items():
                self._process(value, f"{path}.{key}")
        elif isinstance(obj, (list, tuple)):
            for i, item in enumerate(obj):
                self._process(item, f"{path}[{i}]")

    def _add_example(self, path: str, value: Any) -> None:
        """
        Store up to N unique examples per path. Equality is checked by Python ==.
        """
        if self._examples_limit <= 0:
            return
        bucket = self._examples_cache.setdefault(path, [])
        # Skip if we already have enough
        if len(bucket) >= self._examples_limit:
            return
        # Avoid duplicates by simple equality
        for existing in bucket:
            if existing == value:
                return
        bucket.append(value)

    def _inject_annotations(self, schema: Dict[str, Any], path: str) -> None:
        """
        Walk the generated schema and inject `format` and `examples` at the right nodes.
        """
        node_type = schema.get("type")

        # ---- Emit format (only for strings, only when unambiguous) ----
        if node_type == "string" and self._format_mode in ("on", "safe"):
            detected_set = self._format_cache.get(path)
            if detected_set and len(detected_set) == 1:
                schema["format"] = next(iter(detected_set))

        # ---- Emit examples (for any node type) ----
        if self._examples_limit > 0:
            ex = self._examples_cache.get(path)
            if ex:
                schema["examples"] = ex[: self._examples_limit]

        # ---- Recurse into composites ----
        if node_type == "object" and "properties" in schema:
            for prop_name, prop_schema in list(schema["properties"].items()):
                self._inject_annotations(prop_schema, f"{path}.{prop_name}")

        # Arrays
        if node_type == "array" and "items" in schema:
            items = schema["items"]
            if isinstance(items, dict):
                self._inject_annotations(items, f"{path}[0]")
            elif isinstance(items, list):
                for i, sub in enumerate(items):
                    self._inject_annotations(sub, f"{path}[{i}]")

        # anyOf / oneOf / allOf (inject on subschemas too)
        for keyword in ("anyOf", "oneOf", "allOf"):
            if keyword in schema:
                for i, sub_schema in enumerate(schema[keyword]):
                    self._inject_annotations(sub_schema, path)
