import logging
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional, Set, Tuple, Union

import pytest

from .core import SchemaShot
from .stats import GLOBAL_STATS, SchemaStats

# Глобальное хранилище экземпляров SchemaShot для различных директорий
_schema_managers: Dict[Path, SchemaShot] = {}


def pytest_addoption(parser: pytest.Parser) -> None:
    """Добавляет опцию --schema-update в pytest."""
    parser.addoption(
        "--schema-update",
        action="store_true",
        help="Обновить или создать JSON Schema файлы на основе текущих данных",
    )
    parser.addini(
        "schema_shot_dir",
        default="__snapshots__",
        help="Директория для хранения схем (по умолчанию: __snapshots__)",
    )


@pytest.fixture(scope="function")
def schemashot(request: pytest.FixtureRequest) -> Generator[SchemaShot, None, None]:
    """
    Фикстура, предоставляющая экземпляр SchemaShot и собирающая использованные схемы.
    """
    global _schema_managers, GLOBAL_STATS

    # Получаем путь к тестовому файлу
    test_path = Path(
        request.node.path if hasattr(request.node, "path") else request.node.fspath
    )
    root_dir = test_path.parent
    update_mode = bool(request.config.getoption("--schema-update"))

    # Получаем настраиваемую директорию для схем
    schema_dir_name = str(request.config.getini("schema_shot_dir") or "__snapshots__")

    # Создаем или получаем экземпляр SchemaShot для этой директории
    if root_dir not in _schema_managers:
        _schema_managers[root_dir] = SchemaShot(root_dir, update_mode, schema_dir_name)

    # Создаем локальный экземпляр для теста
    yield _schema_managers[root_dir]

    # Обновляем глобальный экземпляр использованными схемами из этого теста
    # if root_dir in _schema_managers:
    #    _schema_managers[root_dir].used_schemas.update(_schema_managers[root_dir].used_schemas)


@pytest.hookimpl(trylast=True)
def pytest_unconfigure(config: pytest.Config) -> None:
    """
    Хук, который отрабатывает после завершения всех тестов.
    Очищает глобальные переменные.
    """
    global _schema_managers, GLOBAL_STATS

    # Очищаем словарь
    _schema_managers.clear()
    # Сбрасываем статистику для следующего запуска
    GLOBAL_STATS = SchemaStats()


@pytest.hookimpl(trylast=True)
def pytest_terminal_summary(terminalreporter, exitstatus: int) -> None:
    """
    Добавляет сводку о схемах в финальный отчет pytest в терминале.
    """
    global GLOBAL_STATS, _schema_managers

    # Выполняем cleanup перед показом summary
    if _schema_managers:
        update_mode = bool(terminalreporter.config.getoption("--schema-update"))

        # Вызываем метод очистки неиспользованных схем для каждого экземпляра
        for _root_dir, manager in _schema_managers.items():
            cleanup_unused_schemas(manager, update_mode, GLOBAL_STATS)

    # Используем новую функцию для вывода статистики
    update_mode = bool(terminalreporter.config.getoption("--schema-update"))
    GLOBAL_STATS.print_summary(terminalreporter, update_mode)


def cleanup_unused_schemas(
    manager: SchemaShot, update_mode: bool, stats: Optional[SchemaStats] = None
) -> None:
    """
    Удаляет неиспользованные схемы в режиме обновления и собирает статистику.

    Args:
        manager: Экземпляр SchemaShot
        update_mode: Режим обновления
        stats: Опциональный объект для сбора статистики
    """
    # Если директория снимков не существует, ничего не делаем
    if not manager.snapshot_dir.exists():
        return

    # Перебираем все файлы схем
    all_schemas = list(manager.snapshot_dir.glob("*.schema.json"))

    for schema_file in all_schemas:
        if schema_file.name not in manager.used_schemas:
            if update_mode:
                try:
                    schema_file.unlink()
                    if stats:
                        stats.add_deleted(schema_file.name)
                except OSError as e:
                    # Логируем ошибки удаления, но не прерываем работу
                    manager.logger.warning(
                        f"Failed to delete unused schema {schema_file.name}: {e}"
                    )
                except Exception as e:
                    # Неожиданные ошибки тоже логируем
                    manager.logger.error(
                        f"Unexpected error deleting schema {schema_file.name}: {e}"
                    )
            else:
                if stats:
                    stats.add_unused(schema_file.name)
