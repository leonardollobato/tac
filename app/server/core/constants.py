"""
Configuration constants for file processing.

This module defines constants used for flattening nested JSON/JSONL structures
into flat column names suitable for SQLite tables.

Delimiter Usage:
    - NESTED_FIELD_DELIMITER: Used to flatten nested objects
      Example: {"user": {"name": "John"}} -> column name "user__name"

    - LIST_INDEX_DELIMITER: Used to flatten arrays with index notation
      Example: {"tags": ["a", "b"]} -> columns "tags_0", "tags_1"

Combined Example:
    Input: {"order": {"items": [{"name": "A"}, {"name": "B"}]}}
    Output columns: "order__items_0__name", "order__items_1__name"
"""

# Delimiter used to separate nested object field names
# Example: user.name -> user__name
NESTED_FIELD_DELIMITER = "__"

# Delimiter used to separate list field names from their index
# Example: tags[0] -> tags_0
LIST_INDEX_DELIMITER = "_"
