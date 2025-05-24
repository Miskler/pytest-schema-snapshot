import pytest

@pytest.mark.asyncio
async def test_something(schemashot):
    data = {
        "обязательная": "строка",
        "необязательная": None,
        "словарь": {
            "ключ": "значение",
            "число": 123,
            "булево": True,
            "список": [1, 2, 3],
            "вложенный_словарь": {
                "пустое": None,
            },
            "пустой_словарь": {},
            "пустой_список": [],
            "пустое_значение": "",
            "пустое_число": 0,
            # Добавляем новое поле для обновления схемы
            "дополнительное_поле": "для обновления"
        },
        "сложная_структура": [
            {
                "id": 1,
                "имя": "Иван",
                "почта": "ivan@example.com",
                "возраст": 25,
                "дата": "2023-01-01T12:00:00Z",
                "вложенный_объект": {
                    "ключ": "значение"
                }
            },
            {
                "id": 2,
                "имя": ["Мария", "Анна"],
                "возраст": 30.5,
                "вложенный_объект": {
                    "ключ": "значение",
                    "лишний_ключ": None
                }
            }
        ],
        "разнотипный_массив": [None, "строка", {"ключ": "значение"}]
    }
    schemashot.assert_match(data, "some_schema")

@pytest.mark.asyncio 
async def test_new_schema_creation(schemashot):
    """Тест для создания новой схемы"""
    new_data = {
        "user_id": 12345,
        "username": "test_user",
        "profile": {
            "bio": "Test bio",
            "settings": {
                "theme": "dark",
                "notifications": True
            }
        },
        "tags": ["python", "testing"]
    }
    schemashot.assert_match(new_data, "user_profile_schema")

@pytest.mark.asyncio
async def test_schema_update(schemashot):
    """Тест для обновления существующей схемы"""
    updated_data = {
        "обязательная": "строка",
        "необязательная": None,
        "словарь": {
            "ключ": "значение",
            "число": 123,
            "булево": True,
            "список": [1, 2, 3],
            "вложенный_словарь": {
                "пустое": None,
            },
            "пустой_словарь": {},
            "пустой_список": [],
            "пустое_значение": "",
            "пустое_число": 0,
            # Добавляем новое поле для обновления схемы
            "новое_поле": "новое значение",
            "ещё_одно_поле": "ещё одно значение",
            "числовое_поле": 42
        },
        "сложная_структура": [
            {
                "id": 1,
                "имя": "Иван",
                "почта": "ivan@example.com",
                "возраст": 25,
                "дата": "2023-01-01T12:00:00Z",
                "вложенный_объект": {
                    "ключ": "значение"
                }
            },
            {
                "id": 2,
                "имя": ["Мария", "Анна"],
                "возраст": 30.5,
                "вложенный_объект": {
                    "ключ": "значение",
                    "лишний_ключ": None
                }
            }
        ],
        "разнотипный_массив": [None, "строка", {"ключ": "значение"}]
    }
    schemashot.assert_match(updated_data, "updated_schema")

@pytest.mark.asyncio
async def test_new_feature_schema(schemashot):
    """Тест для создания совершенно новой схемы"""
    feature_data = {
        "feature_id": "new_feature_2025", 
        "enabled": True,
        "config": {
            "timeout": 30.5,
            "retries": 3,
            "endpoints": ["api1", "api2", "api3"]
        },
        "metadata": {
            "created_by": "system",
            "version": "1.0.0"
        }
    }
    schemashot.assert_match(feature_data, "new_feature_schema")

@pytest.mark.asyncio
async def test_api_response_schema(schemashot):
    """Тест для создания схемы API ответа"""
    api_response = {
        "status": "success",
        "code": 200,
        "data": {
            "users": [
                {"id": 1, "name": "Alice", "active": True},
                {"id": 2, "name": "Bob", "active": False}
            ],
            "pagination": {
                "page": 1,
                "total_pages": 5,
                "total_items": 100
            }
        },
        "timestamp": "2025-05-24T12:00:00Z"
    }
    schemashot.assert_match(api_response, "api_response_schema")

def test_creating_brand_new_schema(schemashot):
    """Тест для создания совершенно новой схемы"""
    new_data = {
        "brand_new_id": 999,
        "brand_new_name": "Brand New Test",
        "brand_new_features": ["feature1", "feature2"],
        "brand_new_metadata": {
            "version": "1.0.0",
            "created_at": "2024-01-15",
            "updated_at": "2024-01-16"
        },
        "brand_new_status": "active"
    }
    
    # Этот assert должен создать новую схему в режиме --schema-update
    schemashot.assert_match(new_data, "brand_new_test")

def test_modifying_existing_schema(schemashot):
    """Тест для проверки обновления существующей схемы"""
    # Модифицируем данные для brand_new_test.schema.json
    modified_data = {
        "brand_new_id": 999,
        "brand_new_name": "Brand New Test",
        "brand_new_features": ["feature1", "feature2", "feature3"],  # добавили feature3
        "brand_new_metadata": {
            "version": "2.0.0",  # изменили версию
            "created_at": "2024-01-15",
            "updated_at": "2024-01-16"  # добавили новое поле
        },
        "brand_new_status": "active"  # добавили новое поле
    }
    
    # Этот assert должен обновить существующую схему в режиме --schema-update
    schemashot.assert_match(modified_data, "brand_new_test")
