import pytest


def test_real_schema_update(schemashot):
    """Тест для проверки реального обновления схемы"""
    # Изменяем данные - добавляем еще одно новое поле
    data = {
        "user_email": "test@example.com",
        "admin_email": "admin@domain.org",
        "new_field": "new_value",
        "another_field": "another_value"  # Добавляем еще одно поле
    }
    schemashot.assert_match(data, "email_test")
