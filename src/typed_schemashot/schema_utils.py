from typing import Any, Dict, List, Union, TypeVar, Optional
import json
from dataclasses import dataclass
from . import cfg as CONFIG 


T = TypeVar('T')

@dataclass
class RawSchema:
    type_names: List[str]
    properties: Optional[Dict[str, 'RawSchema']] = None
    items: Optional[List['RawSchema']] = None
    required: Optional[List[str]] = None

def _get_type_name(value: Any) -> str:
    """Получает имя типа для значения."""
    for t, name in CONFIG.type_map.items():
        if isinstance(value, t):
            return name
    raise ValueError(f'Неподдерживаемый тип: {type(value)}')

def merge_schemas(a: RawSchema, b: RawSchema) -> RawSchema:
    """
    Рекурсивно объединяет две RawSchema: 
    - Склеивает type_names,
    - Для объектов объединяет properties, вычеркивая из required те ключи, которые не встретились в обоих,
    - Для массивов объединяет items одним объединённым элементом.
    """
    # Создаём новый объект-схему
    merged = RawSchema(
        type_names=list(dict.fromkeys(a.type_names + b.type_names))
    )

    # Объединяем свойства объекта
    if 'object' in merged.type_names:
        props_a = a.properties or {}
        props_b = b.properties or {}
        all_keys = set(props_a.keys()) | set(props_b.keys())

        merged.properties = {}
        merged_required: List[str] = []
        for key in all_keys:
            pa = props_a.get(key)
            pb = props_b.get(key)
            if pa and pb:
                # Рекурсивно объединяем дочерние схемы
                merged_prop = merge_schemas(pa, pb)
                merged_required.append(key)
            else:
                # Если свойство есть только в одной схеме → необязательное
                merged_prop = pa or pb
            merged.properties[key] = merged_prop

        merged.required = sorted(merged_required) or None

    # Объединяем элементы массива
    if 'array' in merged.type_names:
        items_a = a.items or []
        items_b = b.items or []
        combined: Optional[RawSchema] = None
        for schema in items_a + items_b:
            if combined is None:
                combined = schema
            else:
                combined = merge_schemas(combined, schema)
        merged.items = [combined] if combined else []

    return merged


def gen_schema(data: Any) -> RawSchema:
    """Генерирует RawSchema из данных."""
    from datetime import datetime

    type_name = _get_type_name(data)
    if type_name == 'object':
        # Собираем дочерние схемы
        props = {k: gen_schema(v) for k, v in data.items()}
        return RawSchema(
            type_names=[type_name],
            properties=props,
            required=list(data.keys())
        )

    elif type_name == 'array':
        if not data:
            return RawSchema(type_names=[type_name])

        # Генерируем схемы для каждого элемента
        item_schemas = [gen_schema(item) for item in data]
        # Склеиваем все схемы элементов
        merged = item_schemas[0]
        for schema in item_schemas[1:]:
            merged = merge_schemas(merged, schema)

        return RawSchema(
            type_names=[type_name],
            items=[merged]
        )

    else:
        return RawSchema(type_names=[type_name])


def to_json_schema(raw: RawSchema) -> Dict[str, Any]:
    """Преобразует RawSchema в JSON Schema."""
    schema: Dict[str, Any] = {
        'type': raw.type_names[0] if len(raw.type_names) == 1 else raw.type_names
    }
    
    if raw.properties:
        schema['properties'] = {
            key: to_json_schema(value)
            for key, value in raw.properties.items()
        }
        schema['additionalProperties'] = False
        if raw.required:
            schema['required'] = raw.required
            
    if raw.items:
        schema['items'] = to_json_schema(raw.items[0])
        
    return schema
