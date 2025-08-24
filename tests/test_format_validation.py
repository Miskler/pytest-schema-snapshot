"""
Тест для проверки валидации форматов.
"""


def test_invalid_email_format_validation(schemashot):
    """Тест, который должен провалиться при неправильном email формате"""
    # Создаем правильную схему с email форматом
    valid_data = {"user_email": "test@example.com"}  # Это создаст format: "email"
    schemashot.assert_json_match(valid_data, "strict_email_validation_test")
