import json
import pandas as pd
import sqlite3
import io
import re
from typing import Dict, Any, List, Set
from .sql_security import (
    execute_query_safely,
    validate_identifier,
    SQLSecurityError
)
from .constants import NESTED_FIELD_DELIMITER, LIST_INDEX_DELIMITER

def sanitize_table_name(table_name: str) -> str:
    """
    Sanitize table name for SQLite by removing/replacing bad characters
    and validating against SQL injection
    """
    # Remove file extension if present
    if '.' in table_name:
        table_name = table_name.rsplit('.', 1)[0]
    
    # Replace bad characters with underscores
    sanitized = re.sub(r'[^a-zA-Z0-9_]', '_', table_name)
    
    # Ensure it starts with a letter or underscore
    if sanitized and not sanitized[0].isalpha() and sanitized[0] != '_':
        sanitized = '_' + sanitized
    
    # Ensure it's not empty
    if not sanitized:
        sanitized = 'table'
    
    # Validate the sanitized name
    try:
        validate_identifier(sanitized, "table")
    except SQLSecurityError:
        # If validation fails, use a safe default
        sanitized = f"table_{hash(table_name) % 100000}"
    
    return sanitized

def convert_csv_to_sqlite(csv_content: bytes, table_name: str) -> Dict[str, Any]:
    """
    Convert CSV file content to SQLite table
    """
    try:
        # Sanitize table name
        table_name = sanitize_table_name(table_name)
        
        # Read CSV into pandas DataFrame
        df = pd.read_csv(io.BytesIO(csv_content))
        
        # Clean column names
        df.columns = [col.lower().replace(' ', '_').replace('-', '_') for col in df.columns]
        
        # Connect to SQLite database
        conn = sqlite3.connect("db/database.db")
        
        # Write DataFrame to SQLite
        df.to_sql(table_name, conn, if_exists='replace', index=False)
        
        # Get schema information using safe query execution
        cursor_info = execute_query_safely(
            conn,
            "PRAGMA table_info({table})",
            identifier_params={'table': table_name}
        )
        columns_info = cursor_info.fetchall()
        
        schema = {}
        for col in columns_info:
            schema[col[1]] = col[2]  # column_name: data_type
        
        # Get sample data using safe query execution
        cursor_sample = execute_query_safely(
            conn,
            "SELECT * FROM {table} LIMIT 5",
            identifier_params={'table': table_name}
        )
        sample_rows = cursor_sample.fetchall()
        column_names = [col[1] for col in columns_info]
        sample_data = [dict(zip(column_names, row)) for row in sample_rows]
        
        # Get row count using safe query execution
        cursor_count = execute_query_safely(
            conn,
            "SELECT COUNT(*) FROM {table}",
            identifier_params={'table': table_name}
        )
        row_count = cursor_count.fetchone()[0]
        
        conn.close()
        
        return {
            'table_name': table_name,
            'schema': schema,
            'row_count': row_count,
            'sample_data': sample_data
        }
        
    except Exception as e:
        raise Exception(f"Error converting CSV to SQLite: {str(e)}")

def convert_json_to_sqlite(json_content: bytes, table_name: str) -> Dict[str, Any]:
    """
    Convert JSON file content to SQLite table
    """
    try:
        # Sanitize table name
        table_name = sanitize_table_name(table_name)
        
        # Parse JSON
        data = json.loads(json_content.decode('utf-8'))
        
        # Ensure it's a list of objects
        if not isinstance(data, list):
            raise ValueError("JSON must be an array of objects")
        
        if not data:
            raise ValueError("JSON array is empty")
        
        # Convert to pandas DataFrame
        df = pd.DataFrame(data)
        
        # Clean column names
        df.columns = [col.lower().replace(' ', '_').replace('-', '_') for col in df.columns]
        
        # Connect to SQLite database
        conn = sqlite3.connect("db/database.db")
        
        # Write DataFrame to SQLite
        df.to_sql(table_name, conn, if_exists='replace', index=False)
        
        # Get schema information using safe query execution
        cursor_info = execute_query_safely(
            conn,
            "PRAGMA table_info({table})",
            identifier_params={'table': table_name}
        )
        columns_info = cursor_info.fetchall()
        
        schema = {}
        for col in columns_info:
            schema[col[1]] = col[2]  # column_name: data_type
        
        # Get sample data using safe query execution
        cursor_sample = execute_query_safely(
            conn,
            "SELECT * FROM {table} LIMIT 5",
            identifier_params={'table': table_name}
        )
        sample_rows = cursor_sample.fetchall()
        column_names = [col[1] for col in columns_info]
        sample_data = [dict(zip(column_names, row)) for row in sample_rows]
        
        # Get row count using safe query execution
        cursor_count = execute_query_safely(
            conn,
            "SELECT COUNT(*) FROM {table}",
            identifier_params={'table': table_name}
        )
        row_count = cursor_count.fetchone()[0]
        
        conn.close()
        
        return {
            'table_name': table_name,
            'schema': schema,
            'row_count': row_count,
            'sample_data': sample_data
        }
        
    except Exception as e:
        raise Exception(f"Error converting JSON to SQLite: {str(e)}")

def flatten_record(record: Dict, prefix: str = "", delimiter: str = NESTED_FIELD_DELIMITER, list_delimiter: str = LIST_INDEX_DELIMITER) -> Dict[str, Any]:
    """
    Recursively flatten a nested dictionary/list structure into a flat dictionary.

    Args:
        record: The dictionary to flatten
        prefix: Current prefix for keys (used in recursion)
        delimiter: Delimiter for nested object fields (default: "__")
        list_delimiter: Delimiter for array indices (default: "_")

    Returns:
        A flat dictionary with all nested values at the root level

    Examples:
        >>> flatten_record({"user": {"name": "John", "age": 30}})
        {"user__name": "John", "user__age": 30}

        >>> flatten_record({"tags": ["a", "b", "c"]})
        {"tags_0": "a", "tags_1": "b", "tags_2": "c"}

        >>> flatten_record({"order": {"items": [{"name": "A"}, {"name": "B"}]}})
        {"order__items_0__name": "A", "order__items_1__name": "B"}
    """
    flat_dict = {}

    for key, value in record.items():
        # Create the new key with prefix if present
        new_key = f"{prefix}{delimiter}{key}" if prefix else key

        if value is None:
            flat_dict[new_key] = None
        elif isinstance(value, dict):
            # Recursively flatten nested dictionaries
            flat_dict.update(flatten_record(value, new_key, delimiter, list_delimiter))
        elif isinstance(value, list):
            # Flatten lists by creating indexed keys
            for i, item in enumerate(value):
                indexed_key = f"{new_key}{list_delimiter}{i}"
                if isinstance(item, dict):
                    # Recursively flatten dict items in the list
                    flat_dict.update(flatten_record(item, indexed_key, delimiter, list_delimiter))
                else:
                    # Direct value for non-dict items
                    flat_dict[indexed_key] = item
        else:
            # Direct value assignment for primitives
            flat_dict[new_key] = value

    return flat_dict

def discover_all_fields(records: List[Dict]) -> Set[str]:
    """
    Discover all possible field names across all records by flattening each record.

    This function scans through all records to find all possible fields, which is
    important for JSONL data where different records may have different schemas.

    Args:
        records: List of dictionaries to scan

    Returns:
        Set of all unique flattened field names found across all records

    Examples:
        >>> records = [
        ...     {"id": 1, "user": {"name": "John"}},
        ...     {"id": 2, "user": {"name": "Jane", "age": 25}},
        ...     {"id": 3, "email": "test@example.com"}
        ... ]
        >>> discover_all_fields(records)
        {"id", "user__name", "user__age", "email"}
    """
    all_fields = set()

    for record in records:
        flat_record = flatten_record(record)
        all_fields.update(flat_record.keys())

    return all_fields

def convert_jsonl_to_sqlite(jsonl_content: bytes, table_name: str) -> Dict[str, Any]:
    """
    Convert JSONL (JSON Lines) file content to SQLite table.

    JSONL files contain one JSON object per line. This function:
    1. Parses each line as a separate JSON object
    2. Discovers all possible fields across all records
    3. Flattens nested objects and arrays using configured delimiters
    4. Creates a single SQLite table with all discovered fields

    Args:
        jsonl_content: Raw bytes content of the JSONL file
        table_name: Name for the SQLite table

    Returns:
        Dictionary containing:
            - table_name: Sanitized table name
            - schema: Column names and their SQLite types
            - row_count: Number of rows in the table
            - sample_data: First 5 rows as list of dictionaries

    Raises:
        Exception: If file is empty, malformed, or cannot be processed

    Examples:
        Content of file:
        {"id": 1, "user": {"name": "John"}}
        {"id": 2, "user": {"name": "Jane", "age": 25}}

        Creates table with columns: id, user__name, user__age
    """
    try:
        # Sanitize table name
        table_name = sanitize_table_name(table_name)

        # Parse JSONL content line by line
        records = []
        content_str = jsonl_content.decode('utf-8')
        lines = content_str.strip().split('\n')

        if not lines or (len(lines) == 1 and not lines[0].strip()):
            raise ValueError("JSONL file is empty")

        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if not line:
                continue  # Skip empty lines
            try:
                record = json.loads(line)
                if not isinstance(record, dict):
                    raise ValueError(f"Line {line_num}: Each line must be a JSON object")
                records.append(record)
            except json.JSONDecodeError as e:
                raise ValueError(f"Line {line_num}: Invalid JSON - {str(e)}")

        if not records:
            raise ValueError("No valid JSON objects found in JSONL file")

        # Discover all possible fields across all records
        all_fields = discover_all_fields(records)

        # Flatten all records
        flattened_records = []
        for record in records:
            flat_record = flatten_record(record)
            # Ensure all discovered fields exist (fill missing with None)
            complete_record = {field: flat_record.get(field, None) for field in all_fields}
            flattened_records.append(complete_record)

        # Convert to pandas DataFrame
        df = pd.DataFrame(flattened_records)

        # Clean column names
        df.columns = [col.lower().replace(' ', '_').replace('-', '_') for col in df.columns]

        # Connect to SQLite database
        conn = sqlite3.connect("db/database.db")

        # Write DataFrame to SQLite
        df.to_sql(table_name, conn, if_exists='replace', index=False)

        # Get schema information using safe query execution
        cursor_info = execute_query_safely(
            conn,
            "PRAGMA table_info({table})",
            identifier_params={'table': table_name}
        )
        columns_info = cursor_info.fetchall()

        schema = {}
        for col in columns_info:
            schema[col[1]] = col[2]  # column_name: data_type

        # Get sample data using safe query execution
        cursor_sample = execute_query_safely(
            conn,
            "SELECT * FROM {table} LIMIT 5",
            identifier_params={'table': table_name}
        )
        sample_rows = cursor_sample.fetchall()
        column_names = [col[1] for col in columns_info]
        sample_data = [dict(zip(column_names, row)) for row in sample_rows]

        # Get row count using safe query execution
        cursor_count = execute_query_safely(
            conn,
            "SELECT COUNT(*) FROM {table}",
            identifier_params={'table': table_name}
        )
        row_count = cursor_count.fetchone()[0]

        conn.close()

        return {
            'table_name': table_name,
            'schema': schema,
            'row_count': row_count,
            'sample_data': sample_data
        }

    except Exception as e:
        raise Exception(f"Error converting JSONL to SQLite: {str(e)}")