"""
Тест для проверки валидации форматов.
"""
import pytest


def test_invalid_email_format_validation(schemashot):
    """Тест, который должен провалиться при неправильном email формате"""
    # Создаем правильную схему с email форматом
    valid_data = {
        "user_email": "test@example.com"  # Это создаст format: "email"
    }
    schemashot.assert_match(valid_data, "strict_email_validation_test")


def test_invalid_email_should_fail():
    """Тест, который проверяет, что неправильный email формат провалит валидацию"""
    from typed_schema_shot.core import SchemaShot
    from pathlib import Path
    import pytest
    
    # Создаем экземпляр SchemaShot вручную
    current_dir = Path(__file__).parent
    shot = SchemaShot(current_dir, update_mode=False)
    
    # Данные с неправильным email форматом
    invalid_data = {
        "user_email": "not-an-email-address"
    }
    
    # Это должно провалиться из-за неправильного формата email
    with pytest.raises(pytest.fail.Exception) as exc_info:
        shot.assert_match(invalid_data, "strict_email_validation_test")
    
    # Проверяем, что ошибка связана с форматом email
    error_message = str(exc_info.value)
    assert "email" in error_message.lower()
    assert "format" in error_message.lower() or "not a 'email'" in error_message
