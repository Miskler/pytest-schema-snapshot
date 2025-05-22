from pathlib import Path
import pytest
from .core import SchemaShot

def pytest_addoption(parser: pytest.Parser) -> None:
    """Добавляет опцию --schema-update в pytest."""
    parser.addoption(
        "--schema-update",
        action="store_true",
        help="Обновить или создать JSON Schema файлы на основе текущих данных"
    )

# Хранилище на уровне плагина
_used_schemas: set[str] = set()

@pytest.fixture
def schemashot(request: pytest.FixtureRequest) -> Generator[SchemaShot, None, None]:
    """
    Фикстура, предоставляющая экземпляр SchemaShot.
    
    Использование:
        def test_something(schemashot):
            data = {"key": "value"}
            schemashot.assert_match(data, "test_name")
    """
    root_dir = Path(request.fspath).parent
    update_mode = bool(request.config.getoption("--schema-update"))
    
    shot = SchemaShot(root_dir, update_mode)
    yield shot
    # Собираем имена, но НЕ удаляем
    _used_schemas.update(shot.used_schemas)

def pytest_sessionfinish(session, exitstatus):
    from .core import SchemaShot
    # Удаляем «лишние» схемы только здесь
    update_mode = bool(session.config.getoption("--schema-update"))
    snapshot_dir = Path(session.config.rootpath) / "__snapshots__"
    for schema_file in snapshot_dir.glob("*.schema.json"):
        if schema_file.name not in _used_schemas and update_mode:
            schema_file.unlink()
