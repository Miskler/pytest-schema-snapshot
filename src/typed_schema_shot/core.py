import json
from pathlib import Path
from typing import Any, Dict, Set
import pytest
from jsonschema import validate, ValidationError, FormatChecker
from .compare_schemas import SchemaComparator
from genson import SchemaBuilder


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
            json.dump(schema, f, indent=2, ensure_ascii=False)

    def _load_schema(self, path: Path) -> Dict[str, Any]:
        """Загружает схему из файла."""
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def assert_match(self, data: Any, name: str) -> None:
        """
        Проверяет соответствие данных схеме.
        
        Args:
            data: Данные для проверки
            name: Имя схемы
        """
        __tracebackhide__ = True  # Прячем эту функцию из стека вызовов pytest
        
        schema_path = self._get_schema_path(name)
        self.used_schemas.add(schema_path.name)
        
        # Генерируем текущую схему
        builder = SchemaBuilder()
        builder.add_object(data)
        current_schema = builder.to_schema()
        
        if not schema_path.exists():
            if not self.update_mode:
                raise pytest.fail.Exception(f"Schema '{name}' not found. Run the test with the --schema-update option to create it.")
            
            self._save_schema(current_schema, schema_path)
            pytest.skip(f"New schema '{name}' has been created.")
            return
            
        # Загружаем существующую схему
        existing_schema = self._load_schema(schema_path)
        
        differences = self._compare_schemas(existing_schema, current_schema)
        # Проверяем, нужно ли обновить схему
        if existing_schema != current_schema and self.update_mode:
            self._save_schema(current_schema, schema_path)
            pytest.skip(f"Schema '{name}' updated.\n\n{differences}")
        else:
            try:
                # Проверяем данные по существующей схеме
                validate(instance=data, schema=existing_schema, format_checker=FormatChecker())
            except ValidationError as e:
                pytest.fail(f"\n\n{differences}\n\nValidation error in '{name}': {e.message}")


    def cleanup_unused_schemas(self) -> None:
        """Удаляет неиспользованные схемы в режиме обновления."""
        for schema_file in self.snapshot_dir.glob("*.schema.json"):
            if schema_file.name not in self.used_schemas:
                if self.update_mode:
                    schema_file.unlink()
                    print(f"Unused schema deleted: {schema_file.name}")
                else:
                    pytest.skip(f"Unused schema found: {schema_file.name}. Use --schema-update to delete it.")

    def _compare_schemas(self, old_schema: Dict[str, Any], new_schema: Dict[str, Any]) -> str:
        """Сравнивает две схемы и возвращает описание различий."""
        return SchemaComparator(old_schema, new_schema).compare()
