## Использование

### 1. Базовый пример

```python
import pytest
from your_api_client import API

def test_api_response(schemashot):
    # Получаем данные от API
    response = API.get_data()
    
    # Проверяем данные против схемы
    schemashot.assert_match(response, "api_response")
```

### 2. Асинхронный пример

```python
import pytest

@pytest.mark.asyncio
async def test_async_api(schemashot):
    data = await async_client.fetch_data()
    schemashot.assert_match(data, "async_data")
```

### 3. Работа с несколькими схемами

```python
def test_multiple_schemas(schemashot):
    user_data = {
        "id": 1, 
        "name": "User", 
        "email": "user@example.com"
    }
    
    order_data = {
        "id": 123,
        "items": [
            {"id": 1, "name": "Item 1", "price": 100},
            {"id": 2, "name": "Item 2", "price": 200}
        ],
        "total": 300
    }
    
    # Проверяем каждую схему отдельно
    schemashot.assert_match(user_data, "user")
    schemashot.assert_match(order_data, "order")
```

### 4. Запуск

При первом запуске создайте схемы с опцией `--schema-update`:

```bash
pytest --schema-update
```

При последующих запусках тесты будут проверять данные по сохраненным схемам:

```bash
pytest
```

### 5. Управление схемами

- Обновление схем: `pytest --schema-update`
- Просмотр изменений: при запуске с `--schema-update` плагин покажет изменения в схемах
- Очистка неиспользуемых схем: при запуске с `--schema-update` плагин автоматически удалит неиспользуемые схемы

Плагин автоматически отслеживает используемые схемы и показывает сводку в конце выполнения тестов.
