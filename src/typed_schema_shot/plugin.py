from pathlib import Path
import pytest
import logging
from typing import Generator
from .core import SchemaShot

# Глобальное хранилище используемых схем в рамках всей сессии
_used_schemas: set[str] = set()


def pytest_addoption(parser: pytest.Parser) -> None:
    """Добавляет опцию --schema-update в pytest."""
    parser.addoption(
        "--schema-update",
        action="store_true",
        help="Обновить или создать JSON Schema файлы на основе текущих данных"
    )


@pytest.fixture(scope="function")
def schemashot(request: pytest.FixtureRequest) -> Generator[SchemaShot, None, None]:
    """
    Фикстура, предоставляющая экземпляр SchemaShot и собирающая использованные схемы.
    """
    root_dir = Path(request.fspath).parent
    update_mode = bool(request.config.getoption("--schema-update"))

    shot = SchemaShot(root_dir, update_mode)
    yield shot
    # собираем имена всех схем, проверенных в этом тесте
    _used_schemas.update(shot.used_schemas)


def pytest_unconfigure(config: pytest.Config) -> None:
    """
    Хук, который отрабатывает после завершения всех тестов.
    Удаляет неиспользованные схемы, если запущено с --schema-update.
    """
    update_mode = bool(config.getoption("--schema-update"))
    root_dir = Path(config.rootpath)
    snapshot_dir = root_dir / '__snapshots__'
    logger = logging.getLogger(__name__)

    if not snapshot_dir.exists():
        return

    for schema_file in snapshot_dir.glob("*.schema.json"):
        if schema_file.name not in _used_schemas:
            if update_mode:
                schema_file.unlink()
                logger.info(f"Unused schema deleted: `{schema_file.name}`")
            else:
                logger.warning(
                    f"Unused schema found: `{schema_file.name}`. "
                    "Use `--schema-update` to remove it."
                )
