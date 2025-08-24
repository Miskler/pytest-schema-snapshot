from pathlib import Path
from typing import Dict, Generator, Optional

import pytest
from jsonschema_diff import ConfigMaker, JsonSchemaDiff
from jsonschema_diff.color import HighlighterPipeline
from jsonschema_diff.color.stages import (MonoLinesHighlighter,
                                          PathHighlighter,
                                          ReplaceGenericHighlighter)

from .core import SchemaShot
from .stats import GLOBAL_STATS, SchemaStats

# Global storage of SchemaShot instances for different directories
_schema_managers: Dict[Path, SchemaShot] = {}


def pytest_addoption(parser: pytest.Parser) -> None:
    """Adds --schema-update option to pytest."""
    parser.addoption(
        "--schema-update",
        action="store_true",
        help="Update or create JSON Schema files based on current data",
    )
    parser.addoption(
        "--save-original",
        action="store_true",
        help="Save original JSON alongside schema (same name, but without `.schema` prefix)",
    )
    parser.addoption(
        "--pss-debug",
        action="store_true",
        help="Show internal exception stack (stops hiding them)",
    )

    parser.addini(
        "jsss_dir",
        default="__snapshots__",
        help="Directory for storing schemas (default: __snapshots__)",
    )
    parser.addini(
        "jsss_callable_regex",
        default="{class_method=.}",
        help="Regex for saving callable part of path",
    )


@pytest.fixture(scope="function")
def schemashot(request: pytest.FixtureRequest) -> Generator[SchemaShot, None, None]:
    """
    Fixture providing a SchemaShot instance and gathering used schemas.
    """
    global _schema_managers, GLOBAL_STATS

    # Получаем путь к тестовому файлу
    test_path = Path(
        request.node.path if hasattr(request.node, "path") else request.node.fspath
    )
    root_dir = test_path.parent
    update_mode = bool(request.config.getoption("--schema-update"))
    save_original = bool(request.config.getoption("--save-original"))
    debug_mode = bool(request.config.getoption("--pss-debug"))

    # Получаем настраиваемую директорию для схем
    schema_dir_name = str(request.config.getini("jsss_dir"))
    callable_regex = str(request.config.getini("jsss_callable_regex"))

    differ = JsonSchemaDiff(
        ConfigMaker.make(),
        HighlighterPipeline(
            [MonoLinesHighlighter(), PathHighlighter(), ReplaceGenericHighlighter()]
        ),
    )

    # Создаем или получаем экземпляр SchemaShot для этой директории
    if root_dir not in _schema_managers:
        _schema_managers[root_dir] = SchemaShot(
            root_dir,
            differ,
            callable_regex,
            update_mode,
            save_original,
            debug_mode,
            schema_dir_name,
        )

    # Создаем локальный экземпляр для теста
    yield _schema_managers[root_dir]


@pytest.hookimpl(trylast=True)
def pytest_unconfigure(config: pytest.Config) -> None:
    """
    Hook that runs after all tests have finished.
    Clears global variables.
    """
    global _schema_managers, GLOBAL_STATS

    # Clear the dictionary
    _schema_managers.clear()
    # Reset stats for next run
    GLOBAL_STATS = SchemaStats()


@pytest.hookimpl(trylast=True)
def pytest_terminal_summary(terminalreporter, exitstatus: int) -> None:
    """
    Adds a summary about schemas to the final pytest report in the terminal.
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
    Deletes unused schemas in update mode and collects statistics.
    Additionally, deletes the pair file `<name>.json` if it exists.

    Args:
        manager: SchemaShot instance
        update_mode: Update mode
        stats: Optional object for collecting statistics
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
                    # Удаляем саму схему
                    schema_file.unlink()
                    if stats:
                        stats.add_deleted(schema_file.name)

                    # Пытаемся удалить парный JSON: <name>.json
                    # Преобразуем "<name>.schema.json" -> "<name>.json"
                    base_name = schema_file.name[: -len(".schema.json")]
                    paired_json = schema_file.with_name(f"{base_name}.json")
                    if paired_json.exists():
                        try:
                            paired_json.unlink()
                            if stats:
                                stats.add_deleted(paired_json.name)
                        except OSError as e:
                            manager.logger.warning(
                                f"Failed to delete paired JSON for {schema_file.name} ({paired_json.name}): {e}"
                            )
                        except Exception as e:
                            manager.logger.error(
                                f"Unexpected error deleting paired JSON for {schema_file.name} ({paired_json.name}): {e}"
                            )

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
