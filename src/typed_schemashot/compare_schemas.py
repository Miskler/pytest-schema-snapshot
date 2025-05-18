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
        self, old: Dict[str, Any], new: Dict[str, Any], path: Optional[List[str]] = None
    ) -> List[Tuple[List[str], Dict[str, Any], Dict[str, Any]]]:
        """Рекурсивно находит различия между двумя схемами."""
        if path is None:
            path = []
        
        differences = []
        all_keys = set(old.keys()) | set(new.keys())
        
        for key in all_keys:
            current_path = path + [key]
            
            if key not in old:
                differences.append((current_path, {}, new[key] if isinstance(new[key], dict) else {key: new[key]}))
            elif key not in new:
                differences.append((current_path, old[key] if isinstance(old[key], dict) else {key: old[key]}, {}))
            elif isinstance(old[key], dict) and isinstance(new[key], dict):
                differences.extend(self._find_differences(old[key], new[key], current_path))
            elif old[key] != new[key]:
                differences.append((
                    current_path,
                    old[key] if isinstance(old[key], dict) else {key: old[key]},
                    new[key] if isinstance(new[key], dict) else {key: new[key]}
                ))
        
        return differences

    @staticmethod
    def _format_path(path: List[str]) -> str:
        """Форматирует путь к изменению."""
        if not path:
            return ""
        result = []
        for item in path:
            if isinstance(item, int):
                result.append(f"[{item}]")
            else:
                result.append(f"[{json.dumps(item, ensure_ascii=False)}]")
        return ''.join(result)

    @staticmethod
    def _format_multiline(prefix: str, value: Any, path: str) -> List[str]:
        """Форматирует многострочное изменение."""
        lines = json.dumps(value, indent=2, ensure_ascii=False).splitlines()
        result = [f"{prefix} {path}:"]
        result.extend(f"{prefix} {line}" for line in lines)
        return result

    @staticmethod
    def _is_simple_value(val: Any) -> bool:
        """Проверяет, является ли значение простым (не структурой)."""
        if not isinstance(val, dict):
            return True
        if len(val) != 1:
            return False
        key = list(val.keys())[0]
        return key == "type" or (isinstance(val[key], (str, int, float, bool, type(None))))

    def _format_differences(
        self, differences: List[Tuple[List[str], Dict[str, Any], Dict[str, Any]]]
    ) -> str:
        """Форматирует найденные различия в читаемый вид."""
        output_lines = []
        
        for path, old_val, new_val in differences:
            parent_path = self._format_path(path)
            
            # Проверяем тип изменения
            if old_val and new_val:  # Changed
                is_simple_change = (
                    isinstance(old_val, dict) and isinstance(new_val, dict) and
                    len(old_val) == 1 and len(new_val) == 1 and
                    list(old_val.keys())[0] == list(new_val.keys())[0] == "type"
                )
                if is_simple_change:
                    old_type = old_val["type"]
                    new_type = new_val["type"]
                    line = f"r {parent_path}: {json.dumps(old_type)} -> {json.dumps(new_type)}"
                    output_lines.append(click.style(line, fg="cyan"))
                else:
                    output_lines.extend(self._format_multiline("-", old_val, parent_path))
                    output_lines.extend(self._format_multiline("+", new_val, parent_path))
            else:  # Added or removed
                if not old_val:  # Added
                    if self._is_simple_value(new_val):
                        val = new_val.get("type", list(new_val.values())[0]) if isinstance(new_val, dict) else new_val
                        line = f"+ {parent_path}: {json.dumps(val)}"
                        output_lines.append(click.style(line, fg="green"))
                    else:
                        output_lines.extend(self._format_multiline("+", new_val, parent_path))
                else:  # Removed
                    if self._is_simple_value(old_val):
                        val = old_val.get("type", list(old_val.values())[0]) if isinstance(old_val, dict) else old_val
                        line = f"- {parent_path}: {json.dumps(val)}"
                        output_lines.append(click.style(line, fg="red"))
                    else:
                        output_lines.extend(self._format_multiline("-", old_val, parent_path))

            # Добавляем пустую строку между изменениями для читаемости
            output_lines.append("")

        return self._colorize_output("\n".join(output_lines).rstrip())

    @staticmethod
    def _colorize_output(text: str) -> str:
        """Добавляет цветовую подсветку к выводу."""
        lines = []
        for line in text.splitlines():
            if line.startswith("+"):
                lines.append(click.style(line, fg="green"))
            elif line.startswith("-"):
                lines.append(click.style(line, fg="red"))
            elif line.startswith("r"):
                lines.append(click.style(line, fg="cyan"))
            else:
                lines.append(line)
        return "\n".join(lines)
