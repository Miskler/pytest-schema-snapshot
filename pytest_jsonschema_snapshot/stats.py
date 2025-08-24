"""
Модуль для сбора и отображения статистики по схемам.
"""

from typing import Any, Dict, List, Optional

from .tools import JsonSchemaDiff


class SchemaStats:
    """Класс для сбора и отображения статистики по схемам"""

    def __init__(self):
        self.created: List[str] = []
        self.updated: List[str] = []
        self.updated_diffs: Dict[str, str] = {}  # schema_name -> diff
        self.uncommitted: List[str] = (
            []
        )  # Новая категория для незафиксированных изменений
        self.uncommitted_diffs: Dict[str, str] = {}  # schema_name -> diff
        self.deleted: List[str] = []
        self.unused: List[str] = []

    def add_created(self, schema_name: str) -> None:
        self.created.append(schema_name)

    def add_updated(
        self,
        schema_name: str,
        old_schema: Optional[Dict[str, Any]] = None,
        new_schema: Optional[Dict[str, Any]] = None,
    ) -> None:
        # Генерируем diff если предоставлены обе схемы
        if old_schema and new_schema:
            diff = JsonSchemaDiff.diff(old_schema, new_schema)
            # Добавляем в updated только если есть реальные изменения
            if diff and diff.strip():
                self.updated.append(schema_name)
                self.updated_diffs[schema_name] = diff
        else:
            # Если схемы не предоставлены, считаем что было обновление
            self.updated.append(schema_name)

    def add_uncommitted(
        self, schema_name: str, old_schema: Dict[str, Any], new_schema: Dict[str, Any]
    ) -> None:
        """Добавляет схему с незафиксированными изменениями"""
        diff = JsonSchemaDiff.diff(old_schema, new_schema)
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
        return bool(
            self.created
            or self.updated
            or self.deleted
            or self.unused
            or self.uncommitted
        )

    def __str__(self) -> str:
        parts = []
        if self.created:
            parts.append(
                f"Созданные схемы ({len(self.created)}): "
                + ", ".join(f"`{s}`" for s in self.created)
            )
        if self.updated:
            parts.append(
                f"Обновленные схемы ({len(self.updated)}): "
                + ", ".join(f"`{s}`" for s in self.updated)
            )
        if self.deleted:
            parts.append(
                f"Удаленные схемы ({len(self.deleted)}): "
                + ", ".join(f"`{s}`" for s in self.deleted)
            )
        if self.unused:
            parts.append(
                f"Неиспользуемые схемы ({len(self.unused)}): "
                + ", ".join(f"`{s}`" for s in self.unused)
            )

        return "\n".join(parts)

    def print_summary(self, terminalreporter, update_mode: bool) -> None:
        """
        Выводит сводку о схемах в финальный отчет pytest в терминале.
        Пары "<name>.schema.json" + "<name>.json" сводятся в одну строку:
        "<name>.schema.json + original" (если original присутствует).
        """

        def _iter_merged(names):
            """
            Итератор по (display, schema_key):
            - display: строка для вывода (возможно с " + original")
            - schema_key: имя файла схемы (<name>.schema.json) для поиска диффов,
                или None, если это не схема.
            Сохраняет порядок оригинального списка: объединение происходит
            в позиции .schema.json; одиночные .json выводятся как есть.
            """
            names = list(names)  # порядок важен
            schema_sfx = ".schema.json"
            json_sfx = ".json"

            # множество баз, где имеются схемы/оригиналы
            bases_with_schema = {
                n[: -len(schema_sfx)] for n in names if n.endswith(schema_sfx)
            }
            bases_with_original = {
                n[: -len(json_sfx)]
                for n in names
                if n.endswith(json_sfx) and not n.endswith(schema_sfx)
            }

            for n in names:
                if n.endswith(schema_sfx):
                    base = n[: -len(schema_sfx)]
                    if base in bases_with_original:
                        yield f"{n} + original", n  # display, schema_key
                    else:
                        yield n, n
                elif n.endswith(json_sfx) and not n.endswith(schema_sfx):
                    base = n[: -len(json_sfx)]
                    # если есть парная схема — .json не выводим отдельно
                    if base in bases_with_schema:
                        continue
                    yield n, None
                else:
                    # на всякий случай — прочие имена
                    yield n, n

        if not self.has_any_info():
            return

        terminalreporter.write_sep("=", "Schema Summary")

        # Created
        if self.created:
            terminalreporter.write_line(
                f"Created schemas ({len(self.created)}):", green=True
            )
            for display, _key in _iter_merged(self.created):
                terminalreporter.write_line(f"  - {display}", green=True)

        # Updated
        if self.updated:
            terminalreporter.write_line(
                f"Updated schemas ({len(self.updated)}):", yellow=True
            )
            for display, key in _iter_merged(self.updated):
                terminalreporter.write_line(f"  - {display}", yellow=True)
                # Показываем diff, если он есть под ключом схемы (.schema.json)
                if key and key in self.updated_diffs:
                    terminalreporter.write_line("    Changes:", yellow=True)
                    for line in self.updated_diffs[key].split("\n"):
                        if line.strip():
                            terminalreporter.write_line(f"      {line}")
                    terminalreporter.write_line("")  # разделение
                elif key:
                    terminalreporter.write_line(
                        "    (Schema unchanged - no differences detected)", cyan=True
                    )

        # Uncommitted
        if self.uncommitted:
            terminalreporter.write_line(
                f"Uncommitted minor updates ({len(self.uncommitted)}):", bold=True
            )
            for display, key in _iter_merged(self.uncommitted):
                terminalreporter.write_line(f"  - {display}", cyan=True)
                if key and key in self.uncommitted_diffs:
                    terminalreporter.write_line("    Detected changes:", cyan=True)
                    for line in self.uncommitted_diffs[key].split("\n"):
                        if line.strip():
                            terminalreporter.write_line(f"      {line}")
                    terminalreporter.write_line("")  # разделение
            terminalreporter.write_line(
                "Use --schema-update to commit these changes", cyan=True
            )

        # Deleted
        if self.deleted:
            terminalreporter.write_line(
                f"Deleted schemas ({len(self.deleted)}):", red=True
            )
            for display, _key in _iter_merged(self.deleted):
                terminalreporter.write_line(f"  - {display}", red=True)

        # Unused (только если не update_mode)
        if self.unused and not update_mode:
            terminalreporter.write_line(f"Unused schemas ({len(self.unused)}):")
            for display, _key in _iter_merged(self.unused):
                terminalreporter.write_line(f"  - {display}")
            terminalreporter.write_line(
                "Use --schema-update to delete unused schemas", yellow=True
            )



GLOBAL_STATS = SchemaStats()
