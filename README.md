# pytest: Typed Schema Shot

![PyPI - Python Version](https://img.shields.io/pypi/pyversions/pytest-typed-schema-shot)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/pytest-typed-schema-shot?label=PyPi%20downloads)](https://pypi.org/project/pytest-typed-schema-shot/)
[![Discord](https://img.shields.io/discord/792572437292253224?label=Discord&labelColor=%232c2f33&color=%237289da)](https://discord.gg/UnJnGHNbBp)
[![Telegram](https://img.shields.io/badge/Telegram-24A1DE)](https://t.me/miskler_dev)

**Plugin for pytest that automatically generates JSON Schemas based on data examples and validates data against saved schemas.**

**Плагин для pytest, который автоматически генерирует JSON Schema на основе примеров данных и проверяет данные по сохраненным схемам.**

## Features

* Automatic JSON Schema generation from data examples (using the `genson` library).

  Автоматическая генерация JSON Schema по примерам данных (на основе библиотеки `genson`).
* Schema storage and management.

  Хранение и управление схемами.
* Validation of data against saved schemas.

  Валидация данных по сохраненным схемам.
* Schema update via `--schema-update` (create new schemas, remove unused ones, update existing).

  Обновление схем через `--schema-update` (создание новых, удаление неиспользуемых, обновление существующих).
* Support for both `async` and synchronous functions.

  Поддержка асинхронных (`async`) и синхронных функций.
* Support for `Union` types and optional fields.

  Поддержка `Union` типов и опциональных полей.

## Installation

```bash
pip install pytest-typed-schema-shot
```

## Usage

1. Use the `schemashot` fixture in your tests

    В тестах используйте фикстуру `schemashot`:

   ```python
   from typed_schema_shot import SchemaShot

   @pytest.mark.asyncio
   async def test_something(schemashot: SchemaShot):
       data = await API.data()
       schemashot.assert_match(data, "data")
   ```

2. On first run, generate schemas with the `--schema-update` flag

    При первом запуске создайте схемы `--schema-update`:

   ```bash
   pytest --schema-update
   ```

3. On subsequent runs, tests will validate data against saved schemas

    В последующих запусках тесты будут проверять данные по сохраненным схемам:

   ```bash
   pytest
   ```

## Key Capabilities

* **Union Types**: support multiple possible types for fields

    Поддержка множественных типов полей.
* **Optional Fields**: automatic detection of required and optional fields

    Автоматическое определение обязательных и необязательных полей.
* **Cleanup**: automatic removal of unused schemas when running in update mode

    Автоматическое удаление неиспользуемых схем в режиме обновления.
