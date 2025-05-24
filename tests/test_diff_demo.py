"""
Демонстрационный тест для проверки диффов в схемах.
"""
import pytest


def test_schema_diff_demo(schemashot):
    """Тест для демонстрации диффа схем"""
    # Измененные данные для демонстрации диффов
    data = {
        "id": "uuid-123-456-789",  # Изменили тип с int на string
        "name": "Updated User",
        "email": "user@example.com",  # Добавили новое поле с email format
        "years": 30,  # Переименовали age в years
        "status": "inactive",  # Изменили значение
        "metadata": {  # Добавили новый объект
            "created_at": "2023-01-01T12:00:00Z",
            "version": "2.0.0"
        }
    }
    schemashot.assert_match(data, "diff_demo_schema")
