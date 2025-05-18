import pytest
from typed_schemashot.schema_utils import (
    RawSchema,
    _get_type_name,
    gen_schema,
    to_json_schema
)

def test_get_type_name():
    """Тестирование определения типов данных."""
    assert _get_type_name(None) == 'null'
    assert _get_type_name(True) == 'boolean'
    assert _get_type_name(42) == 'integer'
    assert _get_type_name(3.14) == 'number'
    assert _get_type_name("test") == 'string'
    assert _get_type_name([1, 2, 3]) == 'array'
    assert _get_type_name({'key': 'value'}) == 'object'
    
    with pytest.raises(ValueError):
        _get_type_name(lambda x: x)

def test_gen_schema_simple_types():
    """Тестирование генерации схемы для простых типов."""
    assert gen_schema(42).type_names == ['integer']
    assert gen_schema("test").type_names == ['string']
    assert gen_schema(None).type_names == ['null']
    assert gen_schema(True).type_names == ['boolean']

def test_gen_schema_array():
    """Тестирование генерации схемы для массивов."""
    # Пустой массив
    empty_array_schema = gen_schema([])
    assert empty_array_schema.type_names == ['array']
    assert empty_array_schema.items is None
    
    # Однородный массив
    numbers_schema = gen_schema([1, 2, 3])
    assert numbers_schema.type_names == ['array']
    assert numbers_schema.items[0].type_names == ['integer']
    
    # Разнородный массив
    mixed_schema = gen_schema([1, "test", True])
    assert mixed_schema.type_names == ['array']
    assert set(mixed_schema.items[0].type_names) == {'integer', 'string', 'boolean'}

def test_gen_schema_object():
    """Тестирование генерации схемы для объектов."""
    data = {
        'name': 'test',
        'value': 42,
        'nested': {
            'key': 'value'
        },
        'options': [1, 1.0, 'one']
    }
    schema = gen_schema(data)
    
    assert schema.type_names == ['object']
    assert set(schema.properties.keys()) == {'name', 'value', 'nested'}
    assert schema.properties['name'].type_names == ['string']
    assert schema.properties['value'].type_names == ['integer']
    assert schema.properties['nested'].type_names == ['object']

    assert schema.properties['nested'].properties['key'].type_names == ['string']

    print(schema.properties['options'])

    assert schema.properties['options'].type_names == ['array']
    assert schema.properties['options'].items[0].type_names == ['integer', 'number', 'string']
    
    assert schema.required == ['name', 'value', 'nested', 'options']

def test_to_json_schema():
    """Тестирование преобразования RawSchema в JSON Schema."""
    raw_schema = RawSchema(
        type_names=['object'],
        properties={
            'name': RawSchema(type_names=['string']),
            'age': RawSchema(type_names=['integer', 'null']),
            'items': RawSchema(
                type_names=['array'],
                items=[RawSchema(type_names=['string', 'number'])]
            )
        },
        required=['name']
    )
    
    json_schema = to_json_schema(raw_schema)
    
    assert json_schema['type'] == 'object'
    assert 'name' in json_schema['properties']
    assert json_schema['properties']['name']['type'] == 'string'
    assert json_schema['properties']['age']['type'] == ['integer', 'null']
    assert json_schema['properties']['items']['type'] == 'array'
    assert json_schema['properties']['items']['items']['type'] == ['string', 'number']
    assert json_schema['required'] == ['name']
    assert json_schema['additionalProperties'] is False
