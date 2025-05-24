"""
Модуль для расширенной генерации JSON Schema с поддержкой format detection.
"""
import re
from typing import Any, Dict, Optional
from genson import SchemaBuilder
from genson.schema.strategies import Object


class FormatDetector:
    """Класс для обнаружения форматов строк"""
    
    # Регулярные выражения для различных форматов
    EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    UUID_PATTERN = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$', re.I)
    DATE_PATTERN = re.compile(r'^\d{4}-\d{2}-\d{2}$')
    DATETIME_PATTERN = re.compile(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})$')
    URI_PATTERN = re.compile(r'^https?://[^\s/$.?#].[^\s]*$', re.I)
    IPV4_PATTERN = re.compile(r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$')
    
    @classmethod
    def detect_format(cls, value: str) -> Optional[str]:
        """
        Определяет формат строки.
        
        Args:
            value: Строка для анализа
            
        Returns:
            Имя формата или None, если формат не определен
        """
        if not isinstance(value, str) or not value:
            return None
            
        # Проверяем форматы в порядке от более специфичных к менее специфичным
        if cls.EMAIL_PATTERN.match(value):
            return "email"
        elif cls.UUID_PATTERN.match(value):
            return "uuid"
        elif cls.DATETIME_PATTERN.match(value):
            return "date-time"
        elif cls.DATE_PATTERN.match(value):
            return "date"
        elif cls.URI_PATTERN.match(value):
            return "uri"
        elif cls.IPV4_PATTERN.match(value):
            return "ipv4"
            
        return None


class FormatAwareString:
    """Стратегия для строк с определением формата"""
    
    def __init__(self):
        self.formats = set()
    
    def match_schema(self, obj: Any) -> bool:
        """Проверяет, подходит ли объект для этой стратегии"""
        return isinstance(obj, str)
    
    def match_object(self, obj: Any) -> bool:
        """Проверяет, подходит ли объект для этой стратегии"""
        return isinstance(obj, str)
    
    def add_object(self, obj: Any) -> None:
        """Добавляет объект для анализа"""
        if isinstance(obj, str):
            detected_format = FormatDetector.detect_format(obj)
            if detected_format:
                self.formats.add(detected_format)
    
    def to_schema(self) -> Dict[str, Any]:
        """Генерирует схему для строки"""
        schema = {"type": "string"}
        
        # Если все строки имеют один и тот же формат, добавляем его в схему
        if len(self.formats) == 1:
            schema["format"] = list(self.formats)[0]
        
        return schema


class EnhancedSchemaBuilder(SchemaBuilder):
    """Расширенный SchemaBuilder с поддержкой format detection"""
    
    def __init__(self, schema_uri: Optional[str] = None):
        if schema_uri:
            super().__init__(schema_uri)
        else:
            super().__init__()
        self._format_cache: Dict[str, set] = {}
    
    def add_object(self, obj: Any, path: str = "root") -> None:
        """
        Добавляет объект в builder с обнаружением форматов.
        
        Args:
            obj: Объект для добавления
            path: Путь к объекту (для внутреннего использования)
        """
        # Сначала вызываем родительский метод
        super().add_object(obj)
        
        # Затем обрабатываем форматы
        self._process_formats(obj, path)
    
    def _process_formats(self, obj: Any, path: str) -> None:
        """Рекурсивно обрабатывает объект для обнаружения форматов"""
        if isinstance(obj, str):
            # Обнаруживаем формат строки
            detected_format = FormatDetector.detect_format(obj)
            if detected_format:
                if path not in self._format_cache:
                    self._format_cache[path] = set()
                self._format_cache[path].add(detected_format)
        elif isinstance(obj, dict):
            # Рекурсивно обрабатываем словарь
            for key, value in obj.items():
                self._process_formats(value, f"{path}.{key}")
        elif isinstance(obj, (list, tuple)):
            # Рекурсивно обрабатываем список
            for i, item in enumerate(obj):
                self._process_formats(item, f"{path}[{i}]")
    
    def to_schema(self) -> Dict[str, Any]:
        """Генерирует схему с учетом обнаруженных форматов"""
        # Получаем базовую схему
        schema = super().to_schema()
        
        # Добавляем форматы
        self._add_formats_to_schema(schema, "root")
        
        return schema
    
    def _add_formats_to_schema(self, schema: Dict[str, Any], path: str) -> None:
        """Рекурсивно добавляет форматы в схему"""
        if schema.get("type") == "string":
            # Если для этого пути есть форматы и все одинаковые
            if path in self._format_cache and len(self._format_cache[path]) == 1:
                schema["format"] = list(self._format_cache[path])[0]
        
        elif schema.get("type") == "object" and "properties" in schema:
            # Рекурсивно обрабатываем свойства объекта
            for prop_name, prop_schema in schema["properties"].items():
                self._add_formats_to_schema(prop_schema, f"{path}.{prop_name}")
        
        elif schema.get("type") == "array" and "items" in schema:
            # Обрабатываем элементы массива
            if isinstance(schema["items"], dict):
                self._add_formats_to_schema(schema["items"], f"{path}[0]")
            elif isinstance(schema["items"], list):
                for i, item_schema in enumerate(schema["items"]):
                    self._add_formats_to_schema(item_schema, f"{path}[{i}]")
        
        elif "anyOf" in schema:
            # Обрабатываем схемы anyOf
            for i, sub_schema in enumerate(schema["anyOf"]):
                self._add_formats_to_schema(sub_schema, path)
