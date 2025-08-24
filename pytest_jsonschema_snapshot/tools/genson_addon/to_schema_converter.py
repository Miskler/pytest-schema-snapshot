"""
Module for advanced JSON Schema generation with format detection support.
"""

import re
from typing import Any, Dict, Optional

from genson import SchemaBuilder
from genson.schema.strategies import Object

from .format_detector import FormatDetector


class FormatAwareString:
    """Strategy for strings with format detection"""

    def __init__(self):
        self.formats = set()

    def match_schema(self, obj: Any) -> bool:
        """Checks if the object matches this strategy"""
        return isinstance(obj, str)

    def match_object(self, obj: Any) -> bool:
        """Checks if the object matches this strategy"""
        return isinstance(obj, str)

    def add_object(self, obj: Any) -> None:
        """Adds an object for analysis"""
        if isinstance(obj, str):
            detected_format = FormatDetector.detect_format(obj)
            if detected_format:
                self.formats.add(detected_format)

    def to_schema(self) -> Dict[str, Any]:
        """Generates a schema for the string"""
        schema = {"type": "string"}

        # If all strings have the same format, add it to the schema
        if len(self.formats) == 1:
            schema["format"] = list(self.formats)[0]

        return schema


class JsonToSchemaConverter(SchemaBuilder):
    """Extended SchemaBuilder with format detection support"""

    def __init__(self, schema_uri: Optional[str] = None):
        if schema_uri:
            super().__init__(schema_uri)
        else:
            super().__init__()
        self._format_cache: Dict[str, set] = {}

    def add_object(self, obj: Any, path: str = "root") -> None:
        """
        Adds an object to the builder with format detection.

        Args:
            obj: Object to add
            path: Path to the object (for internal use)
        """
        # Call the parent method first
        super().add_object(obj)

        # Then process the formats
        self._process_formats(obj, path)

    def _process_formats(self, obj: Any, path: str) -> None:
        """Recursively processes the object for format detection"""
        if isinstance(obj, str):
            # Detect the format of the string
            detected_format = FormatDetector.detect_format(obj)
            if detected_format:
                if path not in self._format_cache:
                    self._format_cache[path] = set()
                self._format_cache[path].add(detected_format)
        elif isinstance(obj, dict):
            # Recursively process the dictionary
            for key, value in obj.items():
                self._process_formats(value, f"{path}.{key}")
        elif isinstance(obj, (list, tuple)):
            # Recursively process the list
            for i, item in enumerate(obj):
                self._process_formats(item, f"{path}[{i}]")

    def to_schema(self) -> Dict[str, Any]:
        """Generates the schema with format detection"""
        # Get the base schema
        schema = super().to_schema()

        # Add the formats
        self._add_formats_to_schema(schema, "root")

        return schema

    def _add_formats_to_schema(self, schema: Dict[str, Any], path: str) -> None:
        """Recursively adds formats to the schema"""
        if schema.get("type") == "string":
            # If there is only one format for this path
            if path in self._format_cache and len(self._format_cache[path]) == 1:
                schema["format"] = list(self._format_cache[path])[0]

        elif schema.get("type") == "object" and "properties" in schema:
            # Recursively process the object properties
            for prop_name, prop_schema in schema["properties"].items():
                self._add_formats_to_schema(prop_schema, f"{path}.{prop_name}")

        elif schema.get("type") == "array" and "items" in schema:
            # Process the array items
            if isinstance(schema["items"], dict):
                self._add_formats_to_schema(schema["items"], f"{path}[0]")
            elif isinstance(schema["items"], list):
                for i, item_schema in enumerate(schema["items"]):
                    self._add_formats_to_schema(item_schema, f"{path}[{i}]")

        elif "anyOf" in schema:
            # Process the anyOf schemas
            for i, sub_schema in enumerate(schema["anyOf"]):
                self._add_formats_to_schema(sub_schema, path)
