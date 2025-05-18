"""
Модуль для сравнения JSON-схем и красивого отображения различий.
"""
from typing import Any, Dict, List, Tuple, Optional
import json
import click


class SchemaComparator:
    """Внутренний класс для сравнения схем."""

    def __init__(self, old_schema: Dict[str, Any], new_schema: Dict[str, Any]):
        self.old_schema = old_schema
        self.new_schema = new_schema

    def compare(self) -> str:
        """Выполняет сравнение схем и возвращает отформатированный результат."""
        differences = self._find_differences(
            {"properties": self.old_schema.get("properties", {})},
            {"properties": self.new_schema.get("properties", {})}
        )
        return self._format_differences(differences)

    def _find_differences(
        self, old: Any, new: Any, path: Optional[List[str]] = None
    ) -> List[Tuple[List[str], Any, Any]]:
        """Рекурсивно находит различия между двумя структурами."""
        if path is None:
            path = []
        diffs: List[Tuple[List[str], Any, Any]] = []

        # Сравнение списков
        if isinstance(old, list) and isinstance(new, list):
            if old != new:
                diffs.append((path, old, new))
            return diffs

        # Сравнение словарей
        all_keys = set(old.keys()) | set(new.keys())
        for key in all_keys:
            current_path = path + [key]
            if key not in old:
                diffs.append((current_path, None, new[key]))
            elif key not in new:
                diffs.append((current_path, old[key], None))
            else:
                ov = old[key]
                nv = new[key]
                if isinstance(ov, dict) and isinstance(nv, dict):
                    diffs.extend(self._find_differences(ov, nv, current_path))
                elif isinstance(ov, list) and isinstance(nv, list):
                    if ov != nv:
                        diffs.append((current_path, ov, nv))
                elif ov != nv:
                    diffs.append((current_path, ov, nv))
        return diffs

    @staticmethod
    def _format_path(path: List[str]) -> str:
        """Форматирует путь к изменению, пропуская 'properties' и 'items', сокращая .type и .required."""
        segments: List[str] = []
        for i, p in enumerate(path):
            if p in ("properties", "items"):
                continue
            # одинаковое условие для type и required
            if p in ("type", "required", "format") and (i == 0 or path[i-1] != "properties"):
                segments.append(f".{p}")
            else:
                segments.append(f"[{json.dumps(p, ensure_ascii=False)}]")
        return ''.join(segments)

    @staticmethod
    def _format_list_diff(path: str, old_list: List[Any], new_list: List[Any]) -> List[str]:
        """Форматирует diff для списков: полный список с пометками +/-."""
        result: List[str] = [click.style(f"  {path}:", fg="reset")]
        old_set = set(old_list)
        new_set = set(new_list)
        # Сохраняем порядок: индексы из нового, затем из старого
        def sort_key(item):
            try:
                return (0, new_list.index(item))
            except ValueError:
                return (1, old_list.index(item))
        all_items = sorted(old_set | new_set, key=sort_key)

        for item in all_items:
            item_str = json.dumps(item, ensure_ascii=False)
            if item in old_set and item not in new_set:
                result.append(click.style(f"-    {item_str},", fg="red"))
            elif item not in old_set and item in new_set:
                result.append(click.style(f"+    {item_str},", fg="green"))
            else:
                result.append(click.style(f"     {item_str},", fg="reset"))

        head, sep, tail = result[-1].rpartition(',')
        result[-1] = head + tail  # Удаляем запятую в конце последнего элемента

        return result

    def _format_differences(
        self, differences: List[Tuple[List[str], Any, Any]]
    ) -> str:
        """Форматирует найденные различия в читаемый вид."""
        output: List[str] = []
        for path, old_val, new_val in differences:
            p = self._format_path(path)
            # Списки
            if isinstance(old_val, list) and isinstance(new_val, list):
                output.extend(self._format_list_diff(p, old_val, new_val))
            # Добавление
            elif old_val is None:
                if isinstance(new_val, list):
                    output.extend(self._format_list_diff(p, [], new_val))
                else:
                    output.append(click.style(f"+ {p}: {json.dumps(new_val, ensure_ascii=False)}", fg="green"))
            # Удаление
            elif new_val is None:
                if isinstance(old_val, list):
                    output.extend(self._format_list_diff(p, old_val, []))
                else:
                    output.append(click.style(f"- {p}: {json.dumps(old_val, ensure_ascii=False)}", fg="red"))
            # Замена простого значения
            elif not isinstance(old_val, (dict, list)) and not isinstance(new_val, (dict, list)):
                output.append(click.style(f"r {p}: {json.dumps(old_val)} -> {json.dumps(new_val)}", fg="cyan"))
            # Сложные структуры
            else:
                old_json = json.dumps(old_val, indent=2, ensure_ascii=False)
                new_json = json.dumps(new_val, indent=2, ensure_ascii=False)
                output.append(f"- {p}:")
                for line in old_json.splitlines():
                    output.append(click.style(f"  {line}", fg="red"))
                output.append(f"+ {p}:")
                for line in new_json.splitlines():
                    output.append(click.style(f"  {line}", fg="green"))
            output.append("")
        return "\n".join(output).rstrip()
