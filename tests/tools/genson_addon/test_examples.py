
import pytest

from pytest_jsonschema_snapshot.tools.genson_addon import JsonToSchemaConverter


def test_examples_limit_and_uniqueness():
    data_points = [
        {"a": "x", "n": 1},
        {"a": "x", "n": 2},
        {"a": "y", "n": 2},
        {"a": "x", "n": 2},  # duplicate
    ]

    conv = JsonToSchemaConverter(format="off", examples=2)
    for d in data_points:
        conv.add_object(d)
    schema = conv.to_schema()
    props = schema["properties"]

    # For "a": up to 2 unique examples among ("x","y")
    assert set(props["a"]["examples"]) <= {"x", "y"}
    assert len(props["a"]["examples"]) <= 2

    # For "n": up to 2 unique examples among (1,2)
    assert set(props["n"]["examples"]) <= {1, 2}
    assert len(props["n"]["examples"]) <= 2

    # Root examples should exist too (entire objects), limited to 2 unique ones
    assert "examples" in schema
    assert len(schema["examples"]) <= 2
    # Every example at root must be a dict resembling added data
    assert all(isinstance(e, dict) and "a" in e and "n" in e for e in schema["examples"])
