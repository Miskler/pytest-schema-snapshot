from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Mapping, TypeAlias, Union

from jsonschema_diff import ConfigMaker
from jsonschema_diff import JsonSchemaDiff as JSD
from jsonschema_diff.color import HighlighterPipeline
from jsonschema_diff.color.stages import (MonoLinesHighlighter,
                                          PathHighlighter,
                                          ReplaceGenericHighlighter)

SchemaLike: TypeAlias = Union[Mapping[str, Any], str, Path]


class JsonSchemaDiff:
    """
    Static, non-instantiable singleton-style helper for JSON Schema diffs.

    - Provides a single public classmethod: `diff(old_schema, new_schema) -> str`.
    - Uses jsonschema-diff under the hood for robust comparison & ANSI highlighting.
    - Caches the result for the *last* (old,new) pair using a content hash.
    """

    # Prevent instantiation
    def __new__(cls, *args, **kwargs):
        raise TypeError(
            "JsonSchemaDiff is static and cannot be instantiated. Use class methods only."
        )

    # Shared, immutable config & color pipeline
    _CONFIG = ConfigMaker.make()
    _PIPELINE = HighlighterPipeline(
        [MonoLinesHighlighter(), ReplaceGenericHighlighter(), PathHighlighter()]
    )

    # Last-call cache
    _last_key: str | None = None
    _last_result: str | None = None

    @classmethod
    def diff(cls, old_schema: SchemaLike, new_schema: SchemaLike) -> str:
        """
        Compare two JSON Schemas and return a colorized, human-readable diff (ANSI).

        Accepts dict-like objects or file paths / JSON strings.
        Uses a stable canonical JSON encoding to compute a BLAKE2b hash and
        returns the cached result if the (old,new) pair matches the previous call.
        """
        old_obj = cls._load_schema(old_schema)
        new_obj = cls._load_schema(new_schema)

        old_bytes = cls._canonical_bytes(old_obj)
        new_bytes = cls._canonical_bytes(new_obj)
        key = cls._hash_pair(old_bytes, new_bytes)

        if key == cls._last_key and cls._last_result is not None:
            return cls._last_result

        differ = JSD(config=cls._CONFIG, colorize_pipeline=cls._PIPELINE)
        differ.compare(old_obj, new_obj)
        result = differ.render()

        cls._last_key = key
        cls._last_result = result
        return result

        # (Optional) could expose a plain/no-color render in the future if needed.

    @classmethod
    def invalidate_cache(cls) -> None:
        """Drop last-call cache explicitly."""
        cls._last_key = None
        cls._last_result = None

    # ----------------- helpers -----------------

    @staticmethod
    def _canonical_bytes(obj: Any) -> bytes:
        """
        Deterministic bytes for hashing:
        - JSON with sorted keys & compact separators for stable canonical form.
        - ensure_ascii=False to avoid escaping non-ASCII (doesn't affect hash stability).
        """
        text = json.dumps(
            obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False
        )
        return text.encode("utf-8")

    @classmethod
    def _hash_pair(cls, a: bytes, b: bytes) -> str:
        """
        Combine two byte-strings into a single BLAKE2b digest.
        Markers (\x00, \x01) avoid collisions for concatenations like (a|b) vs (ab|empty).
        """
        h = hashlib.blake2b(digest_size=32)
        h.update(b"\x00")
        h.update(a)
        h.update(b"\x01")
        h.update(b)
        return h.hexdigest()

    @classmethod
    def _load_schema(cls, src: SchemaLike) -> Dict[str, Any]:
        """
        Load schema from:
          - Mapping (returned as-is)
          - pathlib.Path / str path (read JSON from filesystem)
          - JSON string (if it *looks like* JSON: starts with '{' or '[')
        """
        if isinstance(src, Mapping):
            # Make a shallow copy to avoid external mutations affecting our cache in-place
            return dict(src)

        if isinstance(src, Path):
            return cls._read_json_file(src)

        if isinstance(src, str):
            s = src.strip()
            # First try as a filesystem path
            p = Path(s)
            if p.exists():
                return cls._read_json_file(p)
            # Fallback: treat as inline JSON text
            if s.startswith("{") or s.startswith("["):
                try:
                    loaded = json.loads(s)
                except json.JSONDecodeError as e:
                    raise ValueError(f"Invalid JSON string provided: {e}") from e
                if not isinstance(loaded, (dict, list)):
                    raise ValueError("JSON must be an object or array for a schema.")
                # jsonschema-diff expects dict-like schemas; allow top-level list for arrays
                return loaded  # type: ignore[return-value]
            raise FileNotFoundError(
                f"Schema path does not exist and value is not JSON: {src!r}"
            )

        raise TypeError(
            "Unsupported schema source. Use dict-like, Path, path string, or JSON string."
        )

    @staticmethod
    def _read_json_file(path: Path) -> Dict[str, Any]:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, (dict, list)):
            raise ValueError(f"Schema file must contain JSON object or array: {path}")
        return data  # type: ignore[return-value]
