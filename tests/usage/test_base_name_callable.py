import pytest


def get_data() -> dict:
    return {
        "обязательная": "строка",
        "необязательная": None,
        "словарь": {
            "ключ": "значение",
            "число": 123,
        },
    }


class TestDataClass:
    @staticmethod
    def get_data() -> dict:
        return {
            "обязательная": "строка",
            "необязательная": None,
            "словарь": {
                "ключ": "значение",
                "число": 123,
            },
        }


@pytest.mark.asyncio
async def test_base(schemashot):
    schemashot.assert_json_match(get_data(), get_data)


@pytest.mark.asyncio
async def test_with_class_base(schemashot):
    schemashot.assert_json_match(TestDataClass.get_data(), TestDataClass.get_data)


@pytest.mark.asyncio
async def test_tuple_base(schemashot):
    schemashot.assert_json_match(get_data(), (get_data, "first"))


@pytest.mark.asyncio
async def test_tuple_with_class_base(schemashot):
    schemashot.assert_json_match(TestDataClass.get_data(), (TestDataClass.get_data, "first"))
