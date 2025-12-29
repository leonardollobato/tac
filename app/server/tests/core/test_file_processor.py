import pytest
import json
import pandas as pd
import sqlite3
import os
import io
from pathlib import Path
from unittest.mock import patch
from core.file_processor import convert_csv_to_sqlite, convert_json_to_sqlite, convert_jsonl_to_sqlite, flatten_record, discover_all_fields


@pytest.fixture
def test_db():
    """Create an in-memory test database"""
    # Create in-memory database
    conn = sqlite3.connect(':memory:')
    
    # Patch the database connection to use our in-memory database
    with patch('core.file_processor.sqlite3.connect') as mock_connect:
        mock_connect.return_value = conn
        yield conn
    
    conn.close()


@pytest.fixture
def test_assets_dir():
    """Get the path to test assets directory"""
    return Path(__file__).parent.parent / "assets"


class TestFileProcessor:
    
    def test_convert_csv_to_sqlite_success(self, test_db, test_assets_dir):
        # Load real CSV file
        csv_file = test_assets_dir / "test_users.csv"
        with open(csv_file, 'rb') as f:
            csv_data = f.read()
        
        table_name = "users"
        result = convert_csv_to_sqlite(csv_data, table_name)
        
        # Verify return structure
        assert result['table_name'] == table_name
        assert 'schema' in result
        assert 'row_count' in result
        assert 'sample_data' in result
        
        # Test the returned data
        assert result['row_count'] == 4  # 4 users in test file
        assert len(result['sample_data']) <= 5  # Should return up to 5 samples
        
        # Verify schema has expected columns (cleaned names)
        assert 'name' in result['schema']
        assert 'age' in result['schema'] 
        assert 'city' in result['schema']
        assert 'email' in result['schema']
        
        # Verify sample data structure and content
        john_data = next((item for item in result['sample_data'] if item['name'] == 'John Doe'), None)
        assert john_data is not None
        assert john_data['age'] == 25
        assert john_data['city'] == 'New York'
        assert john_data['email'] == 'john@example.com'
    
    def test_convert_csv_to_sqlite_column_cleaning(self, test_db, test_assets_dir):
        # Test column name cleaning with real file
        csv_file = test_assets_dir / "column_names.csv"
        with open(csv_file, 'rb') as f:
            csv_data = f.read()
        
        table_name = "test_users"
        result = convert_csv_to_sqlite(csv_data, table_name)
        
        # Verify columns were cleaned in the schema
        assert 'full_name' in result['schema']
        assert 'birth_date' in result['schema']
        assert 'email_address' in result['schema']
        assert 'phone_number' in result['schema']
        
        # Verify sample data has cleaned column names and actual content
        sample = result['sample_data'][0]
        assert 'full_name' in sample
        assert 'birth_date' in sample
        assert 'email_address' in sample
        assert sample['full_name'] == 'John Doe'
        assert sample['birth_date'] == '1990-01-15'
    
    def test_convert_csv_to_sqlite_with_inconsistent_data(self, test_db, test_assets_dir):
        # Test with CSV that has inconsistent row lengths - should raise error
        csv_file = test_assets_dir / "invalid.csv"
        with open(csv_file, 'rb') as f:
            csv_data = f.read()
        
        table_name = "inconsistent_table"
        
        # Pandas will fail on inconsistent CSV data
        with pytest.raises(Exception) as exc_info:
            convert_csv_to_sqlite(csv_data, table_name)
        
        assert "Error converting CSV to SQLite" in str(exc_info.value)
    
    def test_convert_json_to_sqlite_success(self, test_db, test_assets_dir):
        # Load real JSON file
        json_file = test_assets_dir / "test_products.json"
        with open(json_file, 'rb') as f:
            json_data = f.read()
        
        table_name = "products"
        result = convert_json_to_sqlite(json_data, table_name)
        
        # Verify return structure
        assert result['table_name'] == table_name
        assert 'schema' in result
        assert 'row_count' in result
        assert 'sample_data' in result
        
        # Test the returned data
        assert result['row_count'] == 3  # 3 products in test file
        assert len(result['sample_data']) == 3
        
        # Verify schema has expected columns
        assert 'id' in result['schema']
        assert 'name' in result['schema']
        assert 'price' in result['schema']
        assert 'category' in result['schema']
        assert 'in_stock' in result['schema']
        
        # Verify sample data structure and content
        laptop_data = next((item for item in result['sample_data'] if item['name'] == 'Laptop'), None)
        assert laptop_data is not None
        assert laptop_data['price'] == 999.99
        assert laptop_data['category'] == 'Electronics'
        assert laptop_data['in_stock'] == True
    
    def test_convert_json_to_sqlite_invalid_json(self):
        # Test with invalid JSON
        json_data = b'invalid json'
        table_name = "test_table"
        
        with pytest.raises(Exception) as exc_info:
            convert_json_to_sqlite(json_data, table_name)
        
        assert "Error converting JSON to SQLite" in str(exc_info.value)
    
    def test_convert_json_to_sqlite_not_array(self):
        # Test with JSON that's not an array
        json_data = b'{"name": "John", "age": 25}'
        table_name = "test_table"
        
        with pytest.raises(Exception) as exc_info:
            convert_json_to_sqlite(json_data, table_name)
        
        assert "JSON must be an array of objects" in str(exc_info.value)
    
    def test_convert_json_to_sqlite_empty_array(self):
        # Test with empty JSON array
        json_data = b'[]'
        table_name = "test_table"

        with pytest.raises(Exception) as exc_info:
            convert_json_to_sqlite(json_data, table_name)

        assert "JSON array is empty" in str(exc_info.value)

    def test_flatten_record(self):
        # Test basic flattening
        record = {"user": {"name": "John", "age": 30}}
        result = flatten_record(record)
        assert result == {"user__name": "John", "user__age": 30}

        # Test array flattening
        record = {"tags": ["a", "b", "c"]}
        result = flatten_record(record)
        assert result == {"tags_0": "a", "tags_1": "b", "tags_2": "c"}

        # Test mixed nested objects and arrays
        record = {"order": {"items": [{"name": "A"}, {"name": "B"}]}}
        result = flatten_record(record)
        assert result == {"order__items_0__name": "A", "order__items_1__name": "B"}

        # Test with None values
        record = {"id": 1, "name": None, "user": {"email": None}}
        result = flatten_record(record)
        assert result == {"id": 1, "name": None, "user__email": None}

        # Test empty dict
        record = {}
        result = flatten_record(record)
        assert result == {}

    def test_discover_all_fields(self):
        # Test field discovery across varying records
        records = [
            {"id": 1, "user": {"name": "John"}},
            {"id": 2, "user": {"name": "Jane", "age": 25}},
            {"id": 3, "email": "test@example.com"}
        ]
        result = discover_all_fields(records)
        assert result == {"id", "user__name", "user__age", "email"}

        # Test with arrays
        records = [
            {"id": 1, "tags": ["a", "b"]},
            {"id": 2, "tags": ["x", "y", "z"]}
        ]
        result = discover_all_fields(records)
        assert "id" in result
        assert "tags_0" in result
        assert "tags_1" in result
        assert "tags_2" in result

        # Test empty list
        records = []
        result = discover_all_fields(records)
        assert result == set()

    def test_convert_jsonl_to_sqlite_simple(self, test_db, test_assets_dir):
        # Load simple JSONL file
        jsonl_file = test_assets_dir / "simple.jsonl"
        with open(jsonl_file, 'rb') as f:
            jsonl_data = f.read()

        table_name = "simple_users"
        result = convert_jsonl_to_sqlite(jsonl_data, table_name)

        # Verify return structure
        assert result['table_name'] == table_name
        assert 'schema' in result
        assert 'row_count' in result
        assert 'sample_data' in result

        # Test the returned data
        assert result['row_count'] == 4  # 4 users in test file
        assert len(result['sample_data']) == 4

        # Verify schema has expected columns
        assert 'id' in result['schema']
        assert 'name' in result['schema']
        assert 'email' in result['schema']
        assert 'age' in result['schema']

        # Verify sample data structure and content
        john_data = next((item for item in result['sample_data'] if item['name'] == 'John Doe'), None)
        assert john_data is not None
        assert john_data['age'] == 30
        assert john_data['email'] == 'john@example.com'

    def test_convert_jsonl_to_sqlite_nested_objects(self, test_db, test_assets_dir):
        # Load JSONL file with nested objects
        jsonl_file = test_assets_dir / "test_events.jsonl"
        with open(jsonl_file, 'rb') as f:
            jsonl_data = f.read()

        table_name = "events"
        result = convert_jsonl_to_sqlite(jsonl_data, table_name)

        # Verify return structure
        assert result['table_name'] == table_name
        assert result['row_count'] == 6  # 6 events in test file

        # Verify nested fields are flattened with __ delimiter
        assert 'event' in result['schema']
        assert 'user__id' in result['schema']
        assert 'user__name' in result['schema']
        assert 'user__email' in result['schema']
        assert 'timestamp' in result['schema']
        assert 'metadata__page' in result['schema']
        assert 'metadata__button' in result['schema']
        assert 'metadata__device' in result['schema']
        assert 'metadata__amount' in result['schema']
        assert 'metadata__currency' in result['schema']

        # Verify values are correctly extracted from nested structure
        login_event = next((item for item in result['sample_data'] if item['event'] == 'login' and item['user__id'] == 1), None)
        assert login_event is not None
        assert login_event['user__name'] == 'John Doe'

        # Verify records with missing fields have None values
        page_view = next((item for item in result['sample_data'] if item['event'] == 'page_view'), None)
        assert page_view is not None
        assert page_view['metadata__page'] == '/home'
        assert page_view['metadata__button'] is None  # Not present in page_view event

    def test_convert_jsonl_to_sqlite_with_arrays(self, test_db, test_assets_dir):
        # Load JSONL file with arrays
        jsonl_file = test_assets_dir / "test_products_nested.jsonl"
        with open(jsonl_file, 'rb') as f:
            jsonl_data = f.read()

        table_name = "products"
        result = convert_jsonl_to_sqlite(jsonl_data, table_name)

        # Verify return structure
        assert result['table_name'] == table_name
        assert result['row_count'] == 5  # 5 products in test file

        # Verify array fields are flattened with index notation
        assert 'id' in result['schema']
        assert 'name' in result['schema']
        assert 'price' in result['schema']
        assert 'tags_0' in result['schema']
        assert 'tags_1' in result['schema']
        assert 'tags_2' in result['schema']
        assert 'tags_3' in result['schema']  # Keyboard has 4 tags

        # Verify values are correctly extracted
        laptop = next((item for item in result['sample_data'] if item['name'] == 'Laptop'), None)
        assert laptop is not None
        assert laptop['tags_0'] == 'electronics'
        assert laptop['tags_1'] == 'computers'
        assert laptop['tags_2'] == 'portable'
        assert laptop['tags_3'] is None  # Laptop only has 3 tags

        # Verify keyboard with 4 tags
        keyboard = next((item for item in result['sample_data'] if item['name'] == 'Keyboard'), None)
        assert keyboard is not None
        assert keyboard['tags_3'] == 'rgb'

    def test_convert_jsonl_to_sqlite_field_discovery(self, test_db):
        # Create JSONL with varying fields across records
        jsonl_data = b'''{"id": 1, "name": "Alice", "email": "alice@example.com"}
{"id": 2, "name": "Bob", "phone": "555-1234"}
{"id": 3, "name": "Charlie", "email": "charlie@example.com", "phone": "555-5678", "city": "NYC"}'''

        table_name = "varying_fields"
        result = convert_jsonl_to_sqlite(jsonl_data, table_name)

        # Verify all fields from all records are discovered
        assert 'id' in result['schema']
        assert 'name' in result['schema']
        assert 'email' in result['schema']
        assert 'phone' in result['schema']
        assert 'city' in result['schema']

        # Verify records with missing fields have None values
        alice = next((item for item in result['sample_data'] if item['name'] == 'Alice'), None)
        assert alice is not None
        assert alice['email'] == 'alice@example.com'
        assert alice['phone'] is None
        assert alice['city'] is None

        bob = next((item for item in result['sample_data'] if item['name'] == 'Bob'), None)
        assert bob is not None
        assert bob['email'] is None
        assert bob['phone'] == '555-1234'

    def test_convert_jsonl_to_sqlite_invalid(self, test_db):
        # Test with invalid JSONL (malformed JSON lines)
        jsonl_data = b'''{"id": 1, "name": "Alice"}
invalid json line
{"id": 2, "name": "Bob"}'''

        table_name = "test_table"

        with pytest.raises(Exception) as exc_info:
            convert_jsonl_to_sqlite(jsonl_data, table_name)

        assert "Error converting JSONL to SQLite" in str(exc_info.value)
        assert "Invalid JSON" in str(exc_info.value)

    def test_convert_jsonl_to_sqlite_empty(self, test_db):
        # Test with empty JSONL file
        jsonl_data = b''
        table_name = "test_table"

        with pytest.raises(Exception) as exc_info:
            convert_jsonl_to_sqlite(jsonl_data, table_name)

        assert "Error converting JSONL to SQLite" in str(exc_info.value)
        assert "empty" in str(exc_info.value).lower()

    def test_convert_jsonl_to_sqlite_not_objects(self, test_db):
        # Test with JSONL where lines are not objects
        jsonl_data = b'''["array", "not", "object"]
{"id": 1, "name": "Valid"}'''

        table_name = "test_table"

        with pytest.raises(Exception) as exc_info:
            convert_jsonl_to_sqlite(jsonl_data, table_name)

        assert "Error converting JSONL to SQLite" in str(exc_info.value)
        assert "must be a JSON object" in str(exc_info.value)