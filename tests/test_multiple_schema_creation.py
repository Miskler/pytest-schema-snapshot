import pytest
from pathlib import Path


def test_multiple_schema_creation(schemashot, pytestconfig):
    """Ensure multiple schemas can be created sequentially."""
    if not pytestconfig.getoption("--schema-update"):
        pytest.skip("requires --schema-update")

    snapshot_dir = Path(__file__).parent / "__snapshots__"
    names = ["multi_schema_one", "multi_schema_two", "multi_schema_three"]

    # Remove existing schemas before the test
    for name in names:
        path = snapshot_dir / f"{name}.schema.json"
        if path.exists():
            path.unlink()

    schemashot.assert_match({"value": 1}, names[0])
    schemashot.assert_match({"value": 2}, names[1])
    schemashot.assert_match({"value": 3}, names[2])

    # Verify all schemas were created
    for name in names:
        assert (snapshot_dir / f"{name}.schema.json").exists(), f"{name} not created"

    # Clean up created schemas
    for name in names:
        (snapshot_dir / f"{name}.schema.json").unlink()
