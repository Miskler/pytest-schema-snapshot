"""
Тест для демонстрации работы диффов схем.
"""
import pytest


def test_user_schema_evolution(schemashot):
    """Тест эволюции схемы пользователя"""
    user_data = {
        "user_id": 12345,  # Изменили тип с string на integer
        "username": "john_doe_updated",  # Изменили значение
        "email": "john@example.com",
        "profile": {
            "first_name": "John",
            "last_name": "Doe", 
            "bio": "Senior Software Engineer",  # Изменили значение
            "avatar_url": "https://example.com/avatar.jpg",
            "age": 30  # Добавили новое поле
        },
        "preferences": {
            "theme": "light",  # Изменили значение
            "language": "en",
            "notifications": False,  # Изменили значение  
            "timezone": "UTC"  # Добавили новое поле
        },
        "created_at": "2023-01-15T10:30:00Z",
        "last_login": "2024-05-24T14:20:00Z",
        "subscription": "premium"  # Добавили новое поле
    }
    schemashot.assert_match(user_data, "user_schema_evolution")


def test_api_response_schema(schemashot):
    """Тест схемы API ответа"""
    api_response = {
        "status": "partial_success",  # Изменили значение еще раз
        "status_code": "200",  # Изменили тип с int на string
        "error_message": "Some warnings occurred",  # Изменили значение
        "warnings": ["Warning 1", "Warning 2"],  # Добавили новое поле - массив
        "data": {
            "users": [
                {
                    "uuid": "550e8400-e29b-41d4-a716-446655440000",  # Заменили id на uuid
                    "full_name": "Alice Johnson",  # Заменили name на full_name
                    "email": "alice@company.com",
                    "role": "admin",
                    "active": True,
                    "permissions": ["read", "write", "admin"]  # Добавили массив разрешений
                }
            ],
            "pagination": {
                "current_page": 1,  # Заменили page на current_page
                "per_page": 10,
                "total": 1,  # Изменили значение
                "has_next": False,
                "has_prev": False
            },
            "filters": {  
                "role": "admin",  # Изменили значение
                "active_only": True,  # Изменили значение
                "department": "engineering"  # Добавили новое поле
            }
        },
        "timestamp": "2024-05-24T15:45:30Z",
        "request_id": "req_67890",  # Изменили значение
        "version": "2.0"  # Добавили новое поле
    }
    schemashot.assert_match(api_response, "api_response_evolution")
