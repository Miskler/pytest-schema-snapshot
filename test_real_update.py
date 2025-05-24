def test_real_schema_update(schemashot):
    """Тест для проверки реального обновления схемы"""
    # Изменяем данные - добавляем новое поле
    data = {
        "user_email": "test@example.com",
        "admin_email": "admin@domain.org",
        "new_field": "new_value"  # Добавляем новое поле
    }
    schemashot.assert_match(data, "email_test")
