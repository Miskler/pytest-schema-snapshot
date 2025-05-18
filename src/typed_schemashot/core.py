import json
import os
from pathlib import Path
from typing import Any, Dict, Set
import pytest
from jsonschema import validate, ValidationError
from .schema_utils import gen_schema, to_json_schema

class SchemaShot:
    def __init__(self, root_dir: Path, update_mode: bool = False):
        """
        Инициализация SchemaShot.
        
        Args:
            root_dir: Корневая директория проекта
            update_mode: Режим обновления схем (--schema-update)
        """
        self.root_dir = root_dir
        self.update_mode = update_mode
        self.snapshot_dir = root_dir / '__snapshots__'
        self.used_schemas: Set[str] = set()
        
        # Создаем директорию для снэпшотов, если её нет
        if not self.snapshot_dir.exists():
            self.snapshot_dir.mkdir(parents=True)

    def _get_schema_path(self, name: str) -> Path:
        """Получает путь к файлу схемы."""
        return self.snapshot_dir / f"{name}.schema.json"

    def _save_schema(self, schema: Dict[str, Any], path: Path) -> None:
        """Сохраняет схему в файл."""
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(schema, f, indent=2)

    def _load_schema(self, path: Path) -> Dict[str, Any]:
        """Загружает схему из файла."""
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _compare_schemas(self, old_schema: Dict[str, Any], new_schema: Dict[str, Any]) -> str:
        """
        Сравнивает две схемы и возвращает описание различий.
        """
        differences = []
        
        def compare_recursive(old: Dict[str, Any], new: Dict[str, Any], path: str = "") -> None:
            if old.get('type') != new.get('type'):
                differences.append(f"{path}: изменение типа с {old.get('type')} на {new.get('type')}")
                
            old_props = old.get('properties', {})
            new_props = new.get('properties', {})
            
            # Проверяем удаленные свойства
            for prop in set(old_props.keys()) - set(new_props.keys()):
                differences.append(f"{path}/{prop}: удалено")
                
            # Проверяем новые свойства
            for prop in set(new_props.keys()) - set(old_props.keys()):
                differences.append(f"{path}/{prop}: добавлено")
                
            # Рекурсивно проверяем общие свойства
            for prop in set(old_props.keys()) & set(new_props.keys()):
                compare_recursive(old_props[prop], new_props[prop], f"{path}/{prop}")
                
        compare_recursive(old_schema, new_schema)
        return "\n".join(differences)

    def assert_match(self, data: Any, name: str) -> None:
        """
        Проверяет соответствие данных схеме.
        
        Args:
            data: Данные для проверки
            name: Имя схемы
        """
        schema_path = self._get_schema_path(name)
        self.used_schemas.add(schema_path.name)
        
        # Генерируем текущую схему
        current_schema = to_json_schema(gen_schema(data))
        
        if not schema_path.exists():
            if not self.update_mode:
                pytest.fail(f"Схема для '{name}' не найдена")
            
            self._save_schema(current_schema, schema_path)
            pytest.skip(f"Создана схема для '{name}'")
            return
            
        # Загружаем существующую схему
        existing_schema = self._load_schema(schema_path)
        
        try:
            # Проверяем данные по существующей схеме
            validate(instance=data, schema=existing_schema)
            
            # Проверяем, нужно ли обновить схему
            if existing_schema != current_schema and self.update_mode:
                differences = self._compare_schemas(existing_schema, current_schema)
                self._save_schema(current_schema, schema_path)
                pytest.skip(f"Схема обновлена для '{name}'\nИзменения:\n{differences}")
                
        except ValidationError as e:
            if self.update_mode:
                self._save_schema(current_schema, schema_path)
                pytest.skip(f"Схема обновлена для '{name}' из-за ошибки валидации")
            else:
                pytest.fail(f"Ошибка валидации: {str(e)}")

    def cleanup_unused_schemas(self) -> None:
        """Удаляет неиспользованные схемы в режиме обновления."""
        if not self.update_mode:
            return
            
        for schema_file in self.snapshot_dir.glob("*.schema.json"):
            if schema_file.name not in self.used_schemas:
                schema_file.unlink()
                print(f"Удалена неиспользуемая схема: {schema_file.name}")
