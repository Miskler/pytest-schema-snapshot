"""
Core logic of the plugin.
"""

import json
import logging
from pathlib import Path
from typing import TYPE_CHECKING, Callable, Iterable, Optional, Set

import pathvalidate

if TYPE_CHECKING:
    from jsonschema_diff import JsonSchemaDiff

import pytest
from jsonschema import FormatChecker, ValidationError, validate

from .stats import GLOBAL_STATS
from .tools import JsonToSchemaConverter, NameMaker


class SchemaShot:
    def __init__(
        self,
        root_dir: Path,
        differ: "JsonSchemaDiff",
        callable_regex: str = "{class_method=.}",
        update_mode: bool = False,
        save_original: bool = False,
        debug_mode: bool = False,
        snapshot_dir_name: str = "__snapshots__",
    ):
        """
        Initializes SchemaShot.

        Args:
            root_dir: Project root directory
            update_mode: Update mode (--schema-update)
            snapshot_dir_name: Name of the directory for snapshots
        """
        self.root_dir: Path = root_dir
        self.differ: "JsonSchemaDiff" = differ
        self.callable_regex: str = callable_regex
        self.update_mode: bool = update_mode
        self.save_original: bool = save_original
        self.debug_mode: bool = debug_mode
        self.snapshot_dir: Path = root_dir / snapshot_dir_name
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

    def _process_name(
        self, name: str | int | Callable | list[str | int | Callable]
    ) -> str:
        """
        1. Converts callable to string
        2. Checks for validity

        Returns:
            str
        Raises:
            ValueError
        """

        __tracebackhide__ = not self.debug_mode  # прячем из стека pytest

        def process_name_part(part: str | int | Callable) -> str:
            if callable(part):
                return NameMaker.format(part, self.callable_regex)
            else:
                return str(part)

        if isinstance(name, (list, tuple)):
            name = ".".join([process_name_part(part) for part in name])
        else:
            name = process_name_part(name)

        if not isinstance(name, str) or not name:
            raise ValueError("Schema name must be a non-empty string")

        try:
            # auto подберёт правила под текущую ОС
            pathvalidate.validate_filename(
                name, platform="auto"
            )  # allow_reserved=False по умолчанию
        except ValidationError as e:
            raise ValueError(f"Invalid schema name: {e}") from None

        return name

    def assert_json_match(
        self,
        data: dict,
        name: str | int | Callable | list[str | int | Callable],
    ) -> Optional[bool]:
        """
        Asserts for JSON, converts it to schema and then compares.

        Returns:
            True  – the schema has been updated,
            False – the schema has not changed,
            None  – a new schema has been created.
        """

        real_name = self._process_name(name)

        builder = JsonToSchemaConverter()
        builder.add_object(data)
        current_schema = builder.to_schema()

        real_name, status = self._base_match(data, current_schema, real_name)

        if self.update_mode:
            json_name = f"{real_name}.json"
            json_path = self.snapshot_dir / json_name

            if self.save_original:
                available_to_create = not json_path.exists() or status is None
                available_to_update = status is True

                if available_to_create or available_to_update:
                    with open(json_path, "w", encoding="utf-8") as f:
                        json.dump(data, f, indent=2, ensure_ascii=False)

                    if available_to_create:
                        GLOBAL_STATS.add_created(json_name)
                    elif available_to_update:
                        GLOBAL_STATS.add_updated(json_name)
                    else:
                        raise ValueError(f"Unexpected status: {status}")
            elif json_path.exists():
                # удаляем
                json_path.unlink()
                GLOBAL_STATS.add_deleted(json_name)

        return status

    def assert_schema_match(
        self,
        schema: dict,
        name: str | int | Callable | list[str | int | Callable],
    ) -> Optional[bool]:
        """
        Accepts a JSON-schema directly and compares it immediately.

        Returns:
            True  – the schema has been updated,
            False – the schema has not changed,
            None  – a new schema has been created.
        """

        real_name = self._process_name(name)

        return self._base_match(None, schema, real_name)[1]

    def _base_match(
        self,
        data: Optional[dict],
        current_schema: dict,
        name: str,
    ) -> tuple[str, Optional[bool]]:
        """
        Checks if data matches the JSON schema, creates/updates it if needed,
        and writes statistics to GLOBAL_STATS.

        Returns:
            True  – the schema has been updated,
            False – the schema has not changed,
            None  – a new schema has been created.
        """
        __tracebackhide__ = not self.debug_mode  # прячем из стека pytest

        # Проверка имени
        name = self._process_name(name)

        schema_path = self.snapshot_dir / f"{name}.schema.json"
        self.used_schemas.add(schema_path.name)

        # --- состояние ДО проверки ---
        schema_exists_before = schema_path.exists()

        # --- когда схемы ещё нет ---
        if not schema_exists_before:
            if not self.update_mode:
                raise pytest.fail.Exception(
                    f"Schema `{name}` not found."
                    "Run the test with the --schema-update option to create it."
                )

            with open(schema_path, "w", encoding="utf-8") as f:
                json.dump(current_schema, f, indent=2, ensure_ascii=False)

            self.logger.info(f"New schema `{name}` has been created.")
            GLOBAL_STATS.add_created(schema_path.name)  # статистика «создана»
            return name, None
        else:
            with open(schema_path, "r", encoding="utf-8") as f:
                existing_schema = json.load(f)

            # --- схема уже была: сравнение и валидация --------------------------------
            schema_updated = False

            if existing_schema != current_schema:  # есть отличия
                differences = self.differ.compare(
                    dict(existing_schema), current_schema
                ).render()

                if self.update_mode:
                    GLOBAL_STATS.add_updated(schema_path.name, differences)

                    # обновляем файл
                    with open(schema_path, "w", encoding="utf-8") as f:
                        json.dump(current_schema, f, indent=2, ensure_ascii=False)
                    self.logger.warning(f"Schema `{name}` updated.\n\n{differences}")
                    schema_updated = True
                elif data is not None:
                    GLOBAL_STATS.add_uncommitted(schema_path.name, differences)

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
            elif data is not None:
                # схемы совпали – всё равно валидируем на случай формальных ошибок
                try:
                    validate(
                        instance=data,
                        schema=existing_schema,
                        format_checker=FormatChecker(),
                    )
                except ValidationError as e:
                    differences = self.differ.compare(
                        dict(existing_schema), current_schema
                    ).render()
                    pytest.fail(
                        f"\n\n{differences}\n\nValidation error in `{name}`: {e.message}"
                    )

            return name, schema_updated
