import re
from typing import Optional


class FormatDetector:
    """Класс для обнаружения форматов строк"""

    # Регулярные выражения для различных форматов
    EMAIL_PATTERN = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
    UUID_PATTERN = re.compile(
        r"^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
        re.I,
    )
    DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")
    DATETIME_PATTERN = re.compile(
        r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})$"
    )
    URI_PATTERN = re.compile(r"^https?://[^\s/$.?#].[^\s]*$", re.I)
    IPV4_PATTERN = re.compile(
        r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$"
    )

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
