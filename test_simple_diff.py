"""
Простой тест для проверки диффов
"""

def test_simple_diff_demo(schemashot):
    """Простой тест для демонстрации диффов"""
    data = {
        "id": 123,
        "name": "Test User"
    }
    schemashot.assert_match(data, "simple_diff_schema")
