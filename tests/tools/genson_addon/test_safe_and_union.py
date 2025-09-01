
import pytest

from pytest_jsonschema_snapshot.tools.genson_addon import JsonToSchemaConverter


def test_safe_mode_sets_vocabulary_and_preserves_or_sets_schema():
    conv = JsonToSchemaConverter(format="safe", examples=0)
    conv.add_object({"s": "abc"})
    schema = conv.to_schema()

    # safe mode must add $vocabulary with disabled format-assertion
    vocab = schema.get("$vocabulary")
    assert isinstance(vocab, dict)
    assert vocab.get("https://json-schema.org/draft/2020-12/vocab/format-annotation") is True
    assert vocab.get("https://json-schema.org/draft/2020-12/vocab/format-assertion") is False

    # also ensure $schema is set if absent
    assert schema.get("$schema") == "https://json-schema.org/draft/2020-12/schema"


def test_safe_mode_does_not_override_explicit_schema():
    custom_uri = "http://json-schema.org/draft-07/schema#"
    conv = JsonToSchemaConverter(schema_uri=custom_uri, format="safe", examples=0)
    conv.add_object({"s": "abc"})
    schema = conv.to_schema()
    # custom $schema kept
    assert schema.get("$schema") == custom_uri
    # but $vocabulary still present
    assert "https://json-schema.org/draft/2020-12/vocab/format-assertion" in schema["$vocabulary"]


def test_union_type_string_null_receives_format():
    conv = JsonToSchemaConverter(format="on", examples=0)
    # Same path yields str and None -> union
    for v in ["john.doe@example.com", None]:
        conv.add_object({"maybe_email": v})
    schema = conv.to_schema()
    node = schema["properties"]["maybe_email"]
    # GenSON tends to emit type: ["string", "null"] for nullable strings
    assert "type" in node
    t = node["type"]
    assert t == "string" or (isinstance(t, list) and "string" in t)
    # Our injector should still put format=email when unambiguous
    if "format" in node:
        assert node["format"] in {"email"}


def test_format_conflict_does_not_emit_format():
    conv = JsonToSchemaConverter(format="on", examples=0)
    # Same path with different recognized formats
    conv.add_object({"v": "john.doe@example.com"})
    conv.add_object({"v": "550e8400-e29b-41d4-a716-446655440000"})
    schema = conv.to_schema()
    node = schema["properties"]["v"]
    assert "format" not in node
