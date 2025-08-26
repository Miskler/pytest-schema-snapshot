
<div align="center">

# 🔍 Pytest JsonSchema SnapShot (JSSS)

<img src="https://raw.githubusercontent.com/Miskler/pytest-jsonschema-snapshot/refs/heads/main/assets/logo.png" width="70%" alt="logo.png" />

*A powerful, intelligent library for comparing JSON schemas with **beautiful formatted output**, **smart parameter combination**, and **contextual information**.*

[![Tests](https://miskler.github.io/pytest-jsonschema-snapshot/tests-badge.svg)](https://miskler.github.io/pytest-jsonschema-snapshot/tests/tests-report.html)
[![Coverage](https://miskler.github.io/pytest-jsonschema-snapshot/coverage.svg)](https://miskler.github.io/pytest-jsonschema-snapshot/coverage/)
[![Python](https://img.shields.io/badge/python-3.10+-blue)](https://python.org)
[![PyPI - Package Version](https://img.shields.io/pypi/v/pytest-jsonschema-snapshot?color=blue)](https://pypi.org/project/pytest-jsonschema-snapshot/)
[![License](https://img.shields.io/badge/license-MIT-blue)](LICENSE)
[![BlackCode](https://img.shields.io/badge/code%20style-black-black)](https://github.com/psf/black)
[![mypy](https://img.shields.io/badge/type--checked-mypy-blue?logo=python)](https://mypy.readthedocs.io/en/stable/index.html)
[![Discord](https://img.shields.io/discord/792572437292253224?label=Discord&labelColor=%232c2f33&color=%237289da)](https://discord.gg/UnJnGHNbBp)
[![Telegram](https://img.shields.io/badge/Telegram-24A1DE)](https://t.me/miskler_dev)


**[⭐ Star us on GitHub](https://github.com/Miskler/pytest-jsonschema-snapshot)** | **[📚 Read the Docs](https://miskler.github.io/pytest-jsonschema-snapshot/basic/quick_start.html)** | **[🐛 Report Bug](https://github.com/Miskler/pytest-jsonschema-snapshot/issues)**

## ✨ Features

</div>




**Plugin for pytest that automatically generates JSON Schemas based on data examples and validates data against saved schemas.**

**Плагин для pytest, который автоматически генерирует JSON Schema на основе примеров данных и проверяет данные по сохраненным схемам.**

![image](https://github.com/user-attachments/assets/2faa2548-5af2-4dc9-8d8d-b32db1d87be8)


## Features

* Automatic JSON Schema generation from data examples (using the `genson` library).

  Автоматическая генерация JSON Schema по примерам данных (на основе библиотеки `genson`).
* **Format detection**: Automatic detection and validation of string formats (email, UUID, date, date-time, URI, IPv4).

  **Обнаружение форматов**: Автоматическое обнаружение и валидация форматов строк (email, UUID, date, date-time, URI, IPv4).
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
* Built-in diff comparison of changes

  Встроенный diff сравнения изменений:
  ```diff
  - ["complex_structure"]["mail"].format: "email"

  r ["complex_structure"]["age"].type:
  -   [
  -     "integer",
  -     "number"
  -   ]
  +   "number"
  
  - ["multitype_array"]: {"key": {"type": "string"}}
  
  - ["multitype_array"].type: "object"
  
  - ["multitype_array"].required:
  -    "ключ"

  + ["multitype_array"].anyOf:
  +    {"type": ["null", "string"]},
  +    {"type": "object", "properties": {"key": {"type": "string"}}, "required": ["key"]}
  ```

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
* **Format Detection**: automatic detection of string formats including:
  - **Email**: `user@example.com` → `{"type": "string", "format": "email"}`
  - **UUID**: `550e8400-e29b-41d4-a716-446655440000` → `{"type": "string", "format": "uuid"}`
  - **Date**: `2023-01-15` → `{"type": "string", "format": "date"}`
  - **Date-Time**: `2023-01-01T12:00:00Z` → `{"type": "string", "format": "date-time"}`
  - **URI**: `https://example.com` → `{"type": "string", "format": "uri"}`
  - **IPv4**: `192.168.1.1` → `{"type": "string", "format": "ipv4"}`

    **Обнаружение форматов**: автоматическое определение форматов строк с поддержкой валидации.
* **Cleanup**: automatic removal of unused schemas when running in update mode

    Автоматическое удаление неиспользуемых схем в режиме обновления.
* **Schema Summary**: colored terminal output showing created, updated, deleted and unused schemas

    Цветной вывод в терминале с информацией о созданных, обновленных, удаленных и неиспользуемых схемах.

## Advanced Usage

### Configuration Options

The plugin supports the following pytest options:
- `--schema-update`: Enable schema update mode (create new, update existing, delete unused schemas)

You can also configure the plugin via `pytest.ini`:

```ini
[tool:pytest]
# Custom directory for storing schemas (default: __snapshots__)
schema_shot_dir = schema_files
```

Or in `pyproject.toml`:

```toml
[tool.pytest.ini_options]
schema_shot_dir = "schema_files"
```

### Schema Summary

The plugin automatically shows a summary at the end of test execution:

```
======== Schema Summary ========
Created schemas (1):
  - new_api_schema.schema.json
Updated schemas (1):  
  - user_profile.schema.json
Unused schemas (2):
  - old_feature.schema.json
  - deprecated_api.schema.json
Use --schema-update to delete unused schemas
```

### Best Practices

1. **Commit schemas to version control**: Schemas should be part of your repository
2. **Review schema changes**: When schemas change, review the diffs carefully
3. **Clean up regularly**: Use `--schema-update` periodically to remove unused schemas
4. **Descriptive names**: Use clear, descriptive names for your schemas

### Troubleshooting

**Schema not found error**: Run tests with `--schema-update` to create missing schemas

**Validation errors**: Check if your data structure has changed and update schemas accordingly

**Permission errors**: Ensure your test directory is writable
