# pytest-typed-schema-shot

Плагин для pytest, который автоматически генерирует JSON Schema на основе примеров данных и проверяет соответствие данных сохраненным схемам.

## Возможности

- 🔄 Автоматическая генерация JSON Schema по примерам данных
- 📸 Хранение схем как снэпшотов
- ✅ Валидация результатов против сохраненных схем
- 🔄 Поддержка обновления схем через `--schema-update`

## Установка

```bash
pip install pytest-typed-schema-shot
```

## Использование

1. В ваших тестах используйте фикстуру `schemashot`:

```python
@pytest.mark.asyncio
async def test_something(schemashot):
    data = await API.data()
    schemashot.assert_match(data, "data")
```

2. При первом запуске используйте флаг `--schema-update` для создания схем:

```bash
pytest --schema-update
```

3. В последующих запусках тесты будут проверять соответствие данных сохраненным схемам:

```bash
pytest
```

## Особенности

- **Union-типы**: поддержка множественных типов для полей
- **Опциональные поля**: автоматическое определение обязательных полей
- **Очистка**: автоматическое удаление неиспользуемых схем при `--schema-update`

## API

### SchemaShot

```python
class SchemaShot:
    def assert_match(self, data: Any, name: str) -> None:
        """
        Проверяет соответствие данных схеме.
        
        Args:
            data: Данные для проверки
            name: Имя схемы
        """
```

## Разработка

1. Клонируйте репозиторий:
```bash
git clone https://github.com/yourusername/pytest-typed-schema-shot.git
cd pytest-typed-schema-shot
```

2. Создайте виртуальное окружение и установите зависимости:
```bash
python -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
```

3. Запустите тесты:
```bash
pytest
```

## Лицензия

MIT
