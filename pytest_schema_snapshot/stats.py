"""
Модуль для сбора и отображения статистики по схемам.
"""
from typing import Dict, List, Any, Optional
from .compare_schemas import SchemaComparator


class SchemaStats:
    """Класс для сбора и отображения статистики по схемам"""
    def __init__(self):
        self.created: List[str] = []
        self.updated: List[str] = []
        self.updated_diffs: Dict[str, str] = {}  # schema_name -> diff
        self.uncommitted: List[str] = []  # Новая категория для незафиксированных изменений
        self.uncommitted_diffs: Dict[str, str] = {}  # schema_name -> diff
        self.deleted: List[str] = []
        self.unused: List[str] = []
        
    def add_created(self, schema_name: str) -> None:
        self.created.append(schema_name)
        
    def add_updated(self, schema_name: str, old_schema: Optional[Dict[str, Any]] = None, new_schema: Optional[Dict[str, Any]] = None) -> None:
        # Генерируем diff если предоставлены обе схемы
        if old_schema and new_schema:
            comparator = SchemaComparator(old_schema, new_schema)
            diff = comparator.compare()
            # Добавляем в updated только если есть реальные изменения
            if diff and diff.strip():
                self.updated.append(schema_name)
                self.updated_diffs[schema_name] = diff
        else:
            # Если схемы не предоставлены, считаем что было обновление
            self.updated.append(schema_name)
    
    def add_uncommitted(self, schema_name: str, old_schema: Dict[str, Any], new_schema: Dict[str, Any]) -> None:
        """Добавляет схему с незафиксированными изменениями"""
        comparator = SchemaComparator(old_schema, new_schema)
        diff = comparator.compare()
        # Добавляем только если есть реальные изменения
        if diff and diff.strip():
            self.uncommitted.append(schema_name)
            self.uncommitted_diffs[schema_name] = diff
        
    def add_deleted(self, schema_name: str) -> None:
        self.deleted.append(schema_name)
        
    def add_unused(self, schema_name: str) -> None:
        self.unused.append(schema_name)
    
    def has_changes(self) -> bool:
        return bool(self.created or self.updated or self.deleted)
    
    def has_any_info(self) -> bool:
        return bool(self.created or self.updated or self.deleted or self.unused or self.uncommitted)
    
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


def print_schema_summary(terminalreporter, schema_stats: SchemaStats, update_mode: bool) -> None:
    """
    Выводит сводку о схемах в финальный отчет pytest в терминале.
    """
    if not schema_stats.has_any_info():
        return
    
    # Добавляем заголовок
    terminalreporter.write_sep("=", "Schema Summary")
    
    # Выводим статистику
    if schema_stats.created:
        terminalreporter.write_line(f"Created schemas ({len(schema_stats.created)}):", green=True)
        for schema in schema_stats.created:
            terminalreporter.write_line(f"  - {schema}", green=True)
    
    if schema_stats.updated:
        terminalreporter.write_line(f"Updated schemas ({len(schema_stats.updated)}):", yellow=True)
        for schema in schema_stats.updated:
            terminalreporter.write_line(f"  - {schema}", yellow=True)
            # Показываем diff если он есть
            if schema in schema_stats.updated_diffs:
                terminalreporter.write_line("    Changes:", yellow=True)
                # Выводим diff построчно с отступом
                for line in schema_stats.updated_diffs[schema].split('\n'):
                    if line.strip():
                        terminalreporter.write_line(f"      {line}")
                terminalreporter.write_line("")  # Пустая строка для разделения
            else:
                terminalreporter.write_line("    (Schema unchanged - no differences detected)", cyan=True)
    
    if schema_stats.uncommitted:
        terminalreporter.write_line(f"Uncommitted minor updates ({len(schema_stats.uncommitted)}):", bold=True)
        for schema in schema_stats.uncommitted:
            terminalreporter.write_line(f"  - {schema}", cyan=True)
            # Показываем diff для незафиксированных изменений
            if schema in schema_stats.uncommitted_diffs:
                terminalreporter.write_line("    Detected changes:", cyan=True)
                # Выводим diff построчно с отступом
                for line in schema_stats.uncommitted_diffs[schema].split('\n'):
                    if line.strip():
                        terminalreporter.write_line(f"      {line}")
                terminalreporter.write_line("")  # Пустая строка для разделения
        terminalreporter.write_line("Use --schema-update to commit these changes", cyan=True)
    
    if schema_stats.deleted:
        terminalreporter.write_line(f"Deleted schemas ({len(schema_stats.deleted)}):", red=True)
        for schema in schema_stats.deleted:
            terminalreporter.write_line(f"  - {schema}", red=True)
    
    if schema_stats.unused and not update_mode:
        terminalreporter.write_line(f"Unused schemas ({len(schema_stats.unused)}):")
        for schema in schema_stats.unused:
            terminalreporter.write_line(f"  - {schema}")
        terminalreporter.write_line("Use --schema-update to delete unused schemas", yellow=True)
