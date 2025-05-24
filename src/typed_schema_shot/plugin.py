from pathlib import Path
import pytest
import logging
from typing import Generator, Dict, Optional, Set, List, Any, Union, Tuple
from .core import SchemaShot
from .stats import SchemaStats, print_schema_summary
from .tracking import TrackedSchemaShot, cleanup_unused_schemas

# Глобальное хранилище экземпляров SchemaShot для различных директорий
_schema_managers: Dict[Path, SchemaShot] = {}


def pytest_addoption(parser: pytest.Parser) -> None:
    """Добавляет опцию --schema-update в pytest."""
    parser.addoption(
        "--schema-update",
        action="store_true",
        help="Обновить или создать JSON Schema файлы на основе текущих данных"
    )
    parser.addini(
        "schema_shot_dir",
        default="__snapshots__",
        help="Директория для хранения схем (по умолчанию: __snapshots__)"
    )


@pytest.fixture(scope="function")
def schemashot(request: pytest.FixtureRequest) -> Generator[SchemaShot, None, None]:
    """
    Фикстура, предоставляющая экземпляр SchemaShot и собирающая использованные схемы.
    """
    global _schema_managers, _schema_stats
    
    # Получаем путь к тестовому файлу
    test_path = Path(request.node.path if hasattr(request.node, 'path') else request.node.fspath)
    root_dir = test_path.parent
    update_mode = bool(request.config.getoption("--schema-update"))
    
    # Получаем настраиваемую директорию для схем
    schema_dir_name = str(request.config.getini("schema_shot_dir") or "__snapshots__")
    
    # Создаем или получаем экземпляр SchemaShot для этой директории
    if root_dir not in _schema_managers:
        _schema_managers[root_dir] = SchemaShot(root_dir, update_mode, schema_dir_name)
    
    # Создаем локальный экземпляр для теста
    shot = TrackedSchemaShot(_schema_managers[root_dir], _schema_stats)
    yield shot
    
    # Обновляем глобальный экземпляр использованными схемами из этого теста
    if root_dir in _schema_managers:
        _schema_managers[root_dir].used_schemas.update(shot.used_schemas)

# Глобальная статистика
_schema_stats = SchemaStats()


@pytest.hookimpl(trylast=True)
def pytest_unconfigure(config: pytest.Config) -> None:
    """
    Хук, который отрабатывает после завершения всех тестов.
    Очищает глобальные переменные.
    """
    global _schema_managers, _schema_stats
    
    # Очищаем словарь
    _schema_managers.clear()
    # Сбрасываем статистику для следующего запуска
    _schema_stats = SchemaStats()


@pytest.hookimpl(trylast=True)
def pytest_terminal_summary(terminalreporter, exitstatus: int) -> None:
    """
    Добавляет сводку о схемах в финальный отчет pytest в терминале.
    """
    global _schema_stats, _schema_managers
    
    # Выполняем cleanup перед показом summary
    if _schema_managers:
        update_mode = bool(terminalreporter.config.getoption("--schema-update"))
        
        # Вызываем метод очистки неиспользованных схем для каждого экземпляра
        for root_dir, manager in _schema_managers.items():
            cleanup_unused_schemas(manager, update_mode, _schema_stats)
    
    # Используем новую функцию для вывода статистики
    update_mode = bool(terminalreporter.config.getoption("--schema-update"))
    print_schema_summary(terminalreporter, _schema_stats, update_mode)
