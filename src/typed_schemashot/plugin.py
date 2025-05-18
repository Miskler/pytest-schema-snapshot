from pathlib import Path
import pytest
from typing import Generator
from .core import SchemaShot

def pytest_addoption(parser: pytest.Parser) -> None:
    """Добавляет опцию --schema-update в pytest."""
    parser.addoption(
        "--schema-update",
        action="store_true",
        help="Обновить или создать JSON Schema файлы на основе текущих данных"
    )

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
    
    # Очистка неиспользуемых схем после завершения тестов
    shot.cleanup_unused_schemas()
