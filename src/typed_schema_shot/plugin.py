from pathlib import Path
import pytest
import logging
from typing import Generator, Dict, Optional, Set, List, Any, Union, Tuple
from .core import SchemaShot
from .compare_schemas import SchemaComparator

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
    schema_dir_name = request.config.getini("schema_shot_dir") or "__snapshots__"
    
    # Создаем или получаем экземпляр SchemaShot для этой директории
    if root_dir not in _schema_managers:
        _schema_managers[root_dir] = SchemaShot(root_dir, update_mode, schema_dir_name)
    
    # Создаем расширенный класс SchemaShot с перехватом событий
    class TrackedSchemaShot(SchemaShot):
        """Расширение SchemaShot с отслеживанием событий для статистики"""
        
        def __init__(self, parent: SchemaShot):
            # Копируем атрибуты из родительского экземпляра
            self.root_dir = parent.root_dir
            self.update_mode = parent.update_mode
            self.snapshot_dir = parent.snapshot_dir
            self.used_schemas = parent.used_schemas
            self.logger = parent.logger
        
        def assert_match(self, data: Any, name: str) -> Optional[bool]:
            """Обертка для отслеживания создания/обновления схем"""
            schema_path = self._get_schema_path(name)
            schema_exists = schema_path.exists()
            
            # Вызываем оригинальный метод
            try:
                result = super().assert_match(data, name)
            except pytest.skip.Exception:
                # Новая схема была создана (pytest.skip вызван в core.py)
                if self.update_mode and not schema_exists and schema_path.exists():
                    _schema_stats.add_created(schema_path.name)
                raise  # Пробрасываем skip дальше
            
            # Отслеживаем события для существующих схем
            if self.update_mode and schema_exists:
                # Если схема была обновлена
                if result is True:
                    _schema_stats.add_updated(schema_path.name)
            
            return result
    
    # Создаем локальный экземпляр для теста
    shot = TrackedSchemaShot(_schema_managers[root_dir])
    yield shot
    
    # Обновляем глобальный экземпляр использованными схемами из этого теста
    if root_dir in _schema_managers:
        _schema_managers[root_dir].used_schemas.update(shot.used_schemas)


class SchemaStats:
    """Класс для сбора и отображения статистики по схемам"""
    def __init__(self):
        self.created: List[str] = []
        self.updated: List[str] = []
        self.updated_diffs: Dict[str, str] = {}  # schema_name -> diff
        self.deleted: List[str] = []
        self.unused: List[str] = []
        
    def add_created(self, schema_name: str) -> None:
        self.created.append(schema_name)
        
    def add_updated(self, schema_name: str, old_schema: Optional[Dict[str, Any]] = None, new_schema: Optional[Dict[str, Any]] = None) -> None:
        self.updated.append(schema_name)
        
        # Генерируем diff если предоставлены обе схемы
        if old_schema and new_schema:
            comparator = SchemaComparator(old_schema, new_schema)
            diff = comparator.compare()
            if diff.strip():  # Только если есть реальные различия
                self.updated_diffs[schema_name] = diff
        
    def add_deleted(self, schema_name: str) -> None:
        self.deleted.append(schema_name)
        
    def add_unused(self, schema_name: str) -> None:
        self.unused.append(schema_name)
    
    def has_changes(self) -> bool:
        return bool(self.created or self.updated or self.deleted)
    
    def has_any_info(self) -> bool:
        return bool(self.created or self.updated or self.deleted or self.unused)
    
    def __str__(self) -> str:
        parts = []
        if self.created:
            parts.append(f"Созданные схемы ({len(self.created)}): " + ", ".join(f"`{s}`" for s in self.created))
        if self.updated:
            parts.append(f"Обновленные схемы ({len(self.updated)}): " + ", ".join(f"`{s}`" for s in self.updated))
        if self.deleted:
            parts.append(f"Удаленные схемы ({len(self.deleted)}): " + ", ".join(f"`{s}`" for s in self.deleted))
        if self.unused:
            parts.append(f"Неиспользуемые схемы ({len(self.unused)}): " + ", ".join(f"`{s}`" for s in self.unused))
        
        return "\n".join(parts)


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
    
    if not _schema_stats.has_any_info():
        return
    
    update_mode = bool(terminalreporter.config.getoption("--schema-update"))
    
    # Добавляем заголовок
    terminalreporter.write_sep("=", "Schema Summary")
    
    # Выводим статистику
    if _schema_stats.created:
        terminalreporter.write_line(f"Created schemas ({len(_schema_stats.created)}):", green=True)
        for schema in _schema_stats.created:
            terminalreporter.write_line(f"  - {schema}", green=True)
    
    if _schema_stats.updated:
        terminalreporter.write_line(f"Updated schemas ({len(_schema_stats.updated)}):", yellow=True)
        for schema in _schema_stats.updated:
            terminalreporter.write_line(f"  - {schema}", yellow=True)
    
    if _schema_stats.deleted:
        terminalreporter.write_line(f"Deleted schemas ({len(_schema_stats.deleted)}):", red=True)
        for schema in _schema_stats.deleted:
            terminalreporter.write_line(f"  - {schema}", red=True)
    
    if _schema_stats.unused and not update_mode:
        terminalreporter.write_line(f"Unused schemas ({len(_schema_stats.unused)}):")
        for schema in _schema_stats.unused:
            terminalreporter.write_line(f"  - {schema}")
        terminalreporter.write_line("Use --schema-update to delete unused schemas", yellow=True)


def cleanup_unused_schemas(manager: SchemaShot, update_mode: bool, stats: Optional[SchemaStats] = None) -> None:
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
                    manager.logger.warning(f"Failed to delete unused schema {schema_file.name}: {e}")
                except Exception as e:
                    # Неожиданные ошибки тоже логируем
                    manager.logger.error(f"Unexpected error deleting schema {schema_file.name}: {e}")
            else:
                if stats:
                    stats.add_unused(schema_file.name)
