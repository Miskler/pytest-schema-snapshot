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

def gen_schema(data: Any) -> RawSchema:
    """Генерирует RawSchema из данных."""
    type_name = _get_type_name(data)
    
    if type_name == 'object':
        properties = {}
        required = []
        
        for key, value in data.items():
            properties[key] = gen_schema(value)
            required.append(key)
            
        return RawSchema(
            type_names=[type_name],
            properties=properties,
            required=required if required else None
        )
        
    elif type_name == 'array':
        if not data:  # Пустой список
            return RawSchema(type_names=[type_name])
            
        item_schemas = [gen_schema(item) for item in data]
        # Объединяем типы элементов
        all_types = set()
        for schema in item_schemas:
            all_types.update(schema.type_names)
            
        return RawSchema(
            type_names=[type_name],
            items=[RawSchema(type_names=list(all_types))]
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
