"""
pytest-typed-schema-shot
========================

Плагин для pytest, который автоматически генерирует JSON Schema
на основе примеров данных и проверяет соответствие данных сохраненным схемам.
"""

from .core import SchemaShot
from .schema_utils import gen_schema, to_json_schema

__version__ = "0.1.0"
__all__ = ["SchemaShot", "gen_schema", "to_json_schema"]
