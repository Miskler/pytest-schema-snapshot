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

## Работа с форматами

### Автоматическое обнаружение форматов

Плагин автоматически обнаруживает и добавляет поля `format` для строк в следующих случаях:

```python
def test_format_detection(schemashot):
    data = {
        "email": "user@example.com",           # format: "email"  
        "id": "550e8400-e29b-41d4-a716-446655440000",  # format: "uuid"
        "birth_date": "1990-01-15",            # format: "date"
        "created_at": "2023-01-01T12:00:00Z",  # format: "date-time" 
        "website": "https://example.com",      # format: "uri"
        "server_ip": "192.168.1.1"            # format: "ipv4"
    }
    schemashot.assert_match(data, "formats_example")
```

Сгенерированная схема будет содержать:

```json
{
  "$schema": "http://json-schema.org/schema#",
  "type": "object", 
  "properties": {
    "email": {
      "type": "string",
      "format": "email"
    },
    "id": {
      "type": "string", 
      "format": "uuid"
    },
    "birth_date": {
      "type": "string",
      "format": "date" 
    },
    "created_at": {
      "type": "string",
      "format": "date-time"
    },
    "website": {
      "type": "string",
      "format": "uri"
    },
    "server_ip": {
      "type": "string", 
      "format": "ipv4"
    }
  }
}
```

### Валидация форматов

При валидации данные проверяются не только по типу, но и по формату:

```python
def test_email_validation(schemashot):
    # Правильный email пройдет валидацию
    valid_data = {"email": "test@example.com"}
    schemashot.assert_match(valid_data, "email_schema")
    
    # Неправильный email вызовет ошибку валидации  
    invalid_data = {"email": "not-an-email"}
    # В режиме без --schema-update это приведет к ошибке:
    # ValidationError: 'not-an-email' is not a 'email'
```
