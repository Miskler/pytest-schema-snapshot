"""
Тесты для обнаружения форматов в JSON Schema.
"""
import pytest


def test_email_format_detection(schemashot):
    """Тест обнаружения email формата"""
    data = {
        "user_email": "test@example.com",
        "admin_email": "admin@domain.org"
    }
    schemashot.assert_match(data, "email_test")


def test_uuid_format_detection(schemashot):
    """Тест обнаружения UUID формата"""
    data = {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "session_id": "6ba7b810-9dad-11d1-80b4-00c04fd430c8"
    }
    schemashot.assert_match(data, "uuid_test")


def test_date_format_detection(schemashot):
    """Тест обнаружения date формата"""
    data = {
        "birth_date": "1990-01-15",
        "registration_date": "2023-12-01"
    }
    schemashot.assert_match(data, "date_test")


def test_datetime_format_detection(schemashot):
    """Тест обнаружения date-time формата"""
    data = {
        "created_at": "2023-01-01T12:00:00Z",
        "updated_at": "2023-12-01T15:30:45.123Z"
    }
    schemashot.assert_match(data, "datetime_test")


def test_uri_format_detection(schemashot):
    """Тест обнаружения URI формата"""
    data = {
        "website": "https://example.com",
        "api_endpoint": "http://api.example.com/v1/users"
    }
    schemashot.assert_match(data, "uri_test")


def test_ipv4_format_detection(schemashot):
    """Тест обнаружения IPv4 формата"""
    data = {
        "server_ip": "192.168.1.1",
        "gateway": "10.0.0.1"
    }
    schemashot.assert_match(data, "ipv4_test")


def test_mixed_formats(schemashot):
    """Тест смешанных форматов в одной схеме"""
    data = {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "email": "user@example.com", 
        "created_at": "2023-01-01T12:00:00Z",
        "birth_date": "1990-01-15",
        "website": "https://example.com",
        "ip_address": "192.168.1.100"
    }
    schemashot.assert_match(data, "mixed_formats_test")


def test_array_format_detection(schemashot):
    """Тест обнаружения форматов в массивах"""
    data = {
        "emails": ["user1@example.com", "user2@example.com", "admin@example.com"],
        "dates": ["2023-01-01", "2023-01-02", "2023-01-03"],
        "uuids": [
            "550e8400-e29b-41d4-a716-446655440000",
            "6ba7b810-9dad-11d1-80b4-00c04fd430c8"
        ]
    }
    schemashot.assert_match(data, "array_formats_test")


def test_no_format_for_regular_strings(schemashot):
    """Тест что обычные строки не получают format"""
    data = {
        "name": "John Doe",
        "description": "This is a regular text string",
        "status": "active"
    }
    schemashot.assert_match(data, "regular_strings_test")
