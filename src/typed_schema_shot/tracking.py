"""
Модуль для отслеживания изменений схем и управления неиспользуемыми схемами.
"""
from pathlib import Path
from typing import Any, Optional
import pytest
from .core import SchemaShot
from .schema_builder import EnhancedSchemaBuilder
from .compare_schemas import SchemaComparator
from .stats import SchemaStats


class TrackedSchemaShot(SchemaShot):
    """Расширение SchemaShot с отслеживанием событий для статистики"""
    
    def __init__(self, parent: SchemaShot, schema_stats: SchemaStats):
        # Копируем атрибуты из родительского экземпляра
        self.root_dir = parent.root_dir
        self.update_mode = parent.update_mode
        self.snapshot_dir = parent.snapshot_dir
        self.used_schemas = parent.used_schemas
        self.logger = parent.logger
        self._schema_stats = schema_stats
    
    def assert_match(self, data: Any, name: str) -> Optional[bool]:
        """Обертка для отслеживания создания/обновления схем"""
        __tracebackhide__ = True  # Прячем эту функцию из стека вызовов pytest

        schema_path = self._get_schema_path(name)
        schema_exists = schema_path.exists()
        
        # Загружаем старую схему если она существует
        old_schema = None
        if schema_exists:
            old_schema = self._load_schema(schema_path)
        
        # Вызываем оригинальный метод
        try:
            result = super().assert_match(data, name)
            
            # Если тест прошел успешно и мы НЕ в режиме обновления,
            # проверяем есть ли незафиксированные изменения
            if not self.update_mode and schema_exists and old_schema:
                # Генерируем схему из текущих данных
                builder = EnhancedSchemaBuilder()
                builder.add_object(data)
                current_schema = builder.to_schema()
                
                # Сравниваем с существующей схемой
                self._schema_stats.add_uncommitted(schema_path.name, old_schema, current_schema)
            
        except pytest.skip.Exception:
            # Новая схема была создана (pytest.skip вызван в core.py)
            if self.update_mode and not schema_exists and schema_path.exists():
                self._schema_stats.add_created(schema_path.name)
            raise  # Пробрасываем skip дальше
        
        # Отслеживаем события для существующих схем в режиме обновления
        if self.update_mode and schema_exists:
            # Загружаем новую схему для сравнения (схема могла быть обновлена)
            new_schema = self._load_schema(schema_path)
            self._schema_stats.add_updated(schema_path.name, old_schema, new_schema)
        
        return result


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
