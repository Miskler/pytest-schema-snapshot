
import pytest

from pytest_jsonschema_snapshot.tools.genson_addon import JsonToSchemaConverter


SAMPLE = {
    "email": "john.doe@example.com",
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "created": "2024-12-31T23:59:59Z",
    "count": 3,
    "profile": {"site": "https://example.org", "ip": "192.168.0.1"},
    "tags": ["one", "two", "three"],
}


@pytest.mark.parametrize("mode", ["off", "on", "safe"])
def test_format_modes_behaviour(mode):
    conv = JsonToSchemaConverter(format=mode, examples=0)
    conv.add_object(SAMPLE)
    schema = conv.to_schema()

    # Navigate to properties shortcuts
    props = schema["properties"]

    if mode == "off":
        # No format anywhere for strings we know about
        for key in ("email", "id", "created"):
            assert "format" not in props[key]
    else:
        # "on" and "safe": we expect known formats set
        assert props["email"].get("format") == "email"
        assert props["id"].get("format") in {"uuid", "uuid4", "uuidv4", "uuid-v4", "uuid_v4"}  # allow detector variance
        assert props["created"].get("format") in {"date-time", "datetime"}

        # Nested string formats
        assert props["profile"]["properties"]["site"].get("format") in {"uri", "url"}
        assert props["profile"]["properties"]["ip"].get("format") in {"ipv4"}

    # Array items shouldn't crash; tags are strings but with no deterministic format
    assert "items" in props["tags"]
    assert "format" not in props["tags"]["items"]
