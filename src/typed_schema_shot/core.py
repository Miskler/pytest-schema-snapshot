import json
from pathlib import Path
from typing import Any, Dict, Set, Optional
import pytest
from jsonschema import validate, ValidationError, FormatChecker
from .compare_schemas import SchemaComparator
from .schema_builder import EnhancedSchemaBuilder
import logging


class SchemaShot:
    def __init__(self, root_dir: Path, update_mode: bool = False, snapshot_dir_name: str = "__snapshots__"):
        """
        Инициализация SchemaShot.
        
        Args:
            root_dir: Корневая директория проекта
            update_mode: Режим обновления схем (--schema-update)
            snapshot_dir_name: Имя директории для снэпшотов
        """
        self.root_dir = root_dir
        self.update_mode = update_mode
        self.snapshot_dir = root_dir / snapshot_dir_name
        self.used_schemas: Set[str] = set()

        self.logger = logging.getLogger(__name__)
        # добавляем вывод в stderr
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(levelname)s %(name)s: %(message)s"))
        self.logger.addHandler(handler)
        # и поднимаем уровень, чтобы INFO/DEBUG прошли через handler
        self.logger.setLevel(logging.INFO)

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

    def assert_match(self, data: Any, name: str) -> Optional[bool]:
        """
        Проверяет соответствие данных схеме.
        
        Args:
            data: Данные для проверки
            name: Имя схемы
            
        Returns:
            True, если схема была обновлена, False, если не было обновления,
            None, если была создана новая схема
            
        Raises:
            ValueError: Если name содержит недопустимые символы
        """
        __tracebackhide__ = True  # Прячем эту функцию из стека вызовов pytest
        
        # Валидация имени схемы
        if not name or not isinstance(name, str):
            raise ValueError("Schema name must be a non-empty string")
        
        # Проверяем на недопустимые символы для имени файла
        invalid_chars = '<>:"/\\|?*'
        if any(char in name for char in invalid_chars):
            raise ValueError(f"Schema name contains invalid characters: {invalid_chars}")
        
        schema_path = self._get_schema_path(name)
        self.used_schemas.add(schema_path.name)
        
        # Генерируем текущую схему
        builder = EnhancedSchemaBuilder()
        builder.add_object(data)
        current_schema = builder.to_schema()
        
        if not schema_path.exists():
            if not self.update_mode:
                raise pytest.fail.Exception(f"Schema `{name}` not found. Run the test with the --schema-update option to create it.")
            
            self._save_schema(current_schema, schema_path)
            pytest.skip(f"New schema `{name}` has been created.")
            return None
            
        # Загружаем существующую схему
        existing_schema = self._load_schema(schema_path)
        
        # Проверяем, нужно ли обновить схему
        schema_updated = False
        if existing_schema != current_schema:
            differences = self._compare_schemas(existing_schema, current_schema)
            
            if self.update_mode:
                self._save_schema(current_schema, schema_path)
                self.logger.warning(f"Schema `{name}` updated.\n\n{differences}")
                schema_updated = True
            else:
                try:
                    # Проверяем данные по существующей схеме
                    validate(instance=data, schema=existing_schema, format_checker=FormatChecker())
                except ValidationError as e:
                    pytest.fail(f"\n\n{differences}\n\nValidation error in `{name}`: {e.message}")
        else:
            # Валидация в любом случае
            try:
                validate(instance=data, schema=existing_schema, format_checker=FormatChecker())
            except ValidationError as e:
                differences = self._compare_schemas(existing_schema, current_schema)
                pytest.fail(f"\n\n{differences}\n\nValidation error in `{name}`: {e.message}")
        
        return schema_updated

    def _compare_schemas(self, old_schema: Dict[str, Any], new_schema: Dict[str, Any]) -> str:
        """Сравнивает две схемы и возвращает описание различий."""
        return SchemaComparator(old_schema, new_schema).compare()
