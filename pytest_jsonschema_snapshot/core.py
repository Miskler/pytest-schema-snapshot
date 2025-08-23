import json
import logging
from pathlib import Path
from typing import Any, Optional, Set

import pytest
from jsonschema import FormatChecker, ValidationError, validate

from .stats import GLOBAL_STATS
from .tools import JsonSchemaDiff, JsonToSchemaConverter, NameValidator


class SchemaShot:
    def __init__(
        self,
        root_dir: Path,
        update_mode: bool = False,
        snapshot_dir_name: str = "__snapshots__",
    ):
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

    def assert_match(self, data: Any, name: str) -> Optional[bool]:
        """
        Проверяет соответствие данных json-схеме, при необходимости создаёт/обновляет её
        и пишет статистику в GLOBAL_STATS.

        Возвращает:
            True  – схема обновлена,
            False – схема не изменилась,
            None  – создана новая схема.
        """
        __tracebackhide__ = True  # прячем из стека pytest

        global GLOBAL_STATS

        # Проверка имени
        NameValidator.check_valid(name)

        schema_path = self.snapshot_dir / f"{name}.schema.json"
        self.used_schemas.add(schema_path.name)

        # --- состояние ДО проверки ------------------------------------------------
        schema_exists_before = schema_path.exists()

        old_schema = None
        if schema_exists_before:
            with open(path, "r", encoding="utf-8") as f:
                old_schema = json.load(f)
        
        # --- строим схему по текущим данным ---------------------------------------
        builder = JsonToSchemaConverter()
        builder.add_object(data)
        current_schema = builder.to_schema()

        # --- когда схемы ещё нет ---------------------------------------------------
        if not schema_exists_before:
            if not self.update_mode:
                raise pytest.fail.Exception(
                    f"Schema `{name}` not found. Run the test with the --schema-update option to create it."
                )

            with open(schema_path, "w", encoding="utf-8") as f:
                json.dump(current_schema, f, indent=2, ensure_ascii=False)

            self.logger.info(f"New schema `{name}` has been created.")
            GLOBAL_STATS.add_created(schema_path.name)  # статистика «создана»
            return None

        # --- схема уже была: сравнение и валидация --------------------------------
        existing_schema = old_schema
        schema_updated = False

        if existing_schema != current_schema:  # есть отличия
            differences = JsonSchemaDiff.diff(existing_schema, current_schema)

            if self.update_mode:
                # обновляем файл
                with open(schema_path, "w", encoding="utf-8") as f:
                    json.dump(current_schema, f, indent=2, ensure_ascii=False)
                self.logger.warning(f"Schema `{name}` updated.\n\n{differences}")
                GLOBAL_STATS.add_updated(  # статистика «обновлена»
                    schema_path.name, old_schema, current_schema
                )
                schema_updated = True
            else:
                # только валидируем по старой схеме
                try:
                    validate(
                        instance=data,
                        schema=existing_schema,
                        format_checker=FormatChecker(),
                    )
                except ValidationError as e:
                    pytest.fail(
                        f"\n\n{differences}\n\nValidation error in `{name}`: {e.message}"
                    )
        else:
            # схемы совпали – всё равно валидируем на случай формальных ошибок
            try:
                validate(
                    instance=data,
                    schema=existing_schema,
                    format_checker=FormatChecker(),
                )
            except ValidationError as e:
                differences = JsonSchemaDiff.diff(existing_schema, current_schema)
                pytest.fail(
                    f"\n\n{differences}\n\nValidation error in `{name}`: {e.message}"
                )

        # --- статистика «незафиксированные изменения» -----------------------------
        if not self.update_mode:
            # пересохранять не стали, но отличия, возможно, есть
            GLOBAL_STATS.add_uncommitted(
                schema_path.name, existing_schema, current_schema
            )

        return schema_updated
