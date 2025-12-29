"""
SQL Security utilities for preventing SQL injection attacks.
Provides functions for safe SQL query execution, identifier validation,
and proper escaping mechanisms.
"""

import re
import sqlite3
from typing import Any, List, Tuple, Optional, Union


class SQLSecurityError(Exception):
    """Raised when SQL security validation fails."""
    pass


def validate_identifier(identifier: str, identifier_type: str = "identifier") -> bool:
    """
    Validate a SQL identifier (table or column name) to prevent injection.
    
    Args:
        identifier: The identifier to validate
        identifier_type: Type of identifier for error messages (e.g., "table", "column")
        
    Returns:
        bool: True if valid, raises SQLSecurityError if invalid
        
    Raises:
        SQLSecurityError: If the identifier contains invalid characters
    """
    if not identifier:
        raise SQLSecurityError(f"Empty {identifier_type} name is not allowed")
    
    # Allow alphanumeric, underscores, and spaces (for column aliases)
    # First character must be letter or underscore
    if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_\s]*$', identifier):
        raise SQLSecurityError(
            f"Invalid {identifier_type} name: '{identifier}'. "
            f"Only alphanumeric characters, underscores, and spaces are allowed."
        )
    
    # Check for SQL keywords that should not be used as identifiers
    sql_keywords = {
        'SELECT', 'FROM', 'WHERE', 'INSERT', 'UPDATE', 'DELETE', 'DROP',
        'CREATE', 'ALTER', 'TABLE', 'DATABASE', 'UNION', 'AND', 'OR',
        'EXEC', 'EXECUTE', 'SCRIPT', 'GRANT', 'REVOKE'
    }
    
    if identifier.upper() in sql_keywords:
        raise SQLSecurityError(
            f"SQL keyword '{identifier}' cannot be used as {identifier_type} name"
        )
    
    return True


def escape_identifier(identifier: str) -> str:
    """
    Safely escape a SQL identifier for use in queries.
    Uses SQLite's square bracket notation for escaping.
    
    Args:
        identifier: The identifier to escape
        
    Returns:
        str: The escaped identifier
    """
    # First validate the identifier
    validate_identifier(identifier)
    
    # In SQLite, identifiers can be quoted with square brackets
    # Double any closing brackets to escape them
    escaped = identifier.replace(']', ']]')
    return f"[{escaped}]"


def execute_query_safely(
    conn: sqlite3.Connection,
    query: str,
    params: Optional[Union[Tuple, List]] = None,
    identifier_params: Optional[dict] = None,
    allow_ddl: bool = False
) -> sqlite3.Cursor:
    """
    Execute a SQL query safely with both value parameters and identifier parameters.
    
    Args:
        conn: SQLite connection object
        query: SQL query with ? placeholders for values and {identifier} for identifiers
        params: Parameters for value placeholders (prevents SQL injection)
        identifier_params: Dictionary of identifier names to be safely escaped
        allow_ddl: If True, allows DDL statements like DROP TABLE (use with caution)
        
    Returns:
        sqlite3.Cursor: The cursor after executing the query
        
    Example:
        execute_query_safely(
            conn,
            "SELECT * FROM {table} WHERE id = ?",
            params=(user_id,),
            identifier_params={'table': table_name}
        )
    """
    # Process identifier parameters if provided
    if identifier_params:
        for key, value in identifier_params.items():
            validate_identifier(value, identifier_type=key)
            # Replace {key} with escaped identifier
            escaped_value = escape_identifier(value)
            query = query.replace(f"{{{key}}}", escaped_value)
    
    # Validate query for dangerous operations unless DDL is explicitly allowed
    if not allow_ddl:
        # Check for DDL operations
        query_upper = query.upper().strip()
        if any(query_upper.startswith(ddl) for ddl in ['DROP', 'CREATE', 'ALTER', 'TRUNCATE']):
            raise SQLSecurityError(
                "DDL operations are not allowed without explicit permission. "
                "Use allow_ddl=True if this is intentional."
            )
    
    # Execute with value parameters
    cursor = conn.cursor()
    if params:
        cursor.execute(query, params)
    else:
        cursor.execute(query)
    
    return cursor


def validate_sql_query(query: str) -> bool:
    """
    Validate a SQL query to ensure it doesn't contain dangerous operations.
    
    Args:
        query: The SQL query to validate
        
    Returns:
        bool: True if safe, raises SQLSecurityError if dangerous
        
    Raises:
        SQLSecurityError: If the query contains dangerous operations
    """
    # Normalize query for checking
    normalized_query = query.upper().strip()
    
    # List of dangerous operations
    dangerous_patterns = [
        r'\bDROP\s+(?:TABLE|DATABASE|INDEX|VIEW)\b',
        r'\bDELETE\s+FROM\b',
        r'\bTRUNCATE\s+TABLE\b',
        r'\bEXEC(?:UTE)?\s*\(',
        r'\bCREATE\s+(?:TABLE|DATABASE|INDEX|VIEW)\b',
        r'\bALTER\s+TABLE\b',
        r'\bGRANT\b',
        r'\bREVOKE\b',
        r'\bINSERT\s+INTO\b.*\bSELECT\b',  # Prevent INSERT...SELECT
        r'\bUPDATE\b.*\bSET\b',
        r';\s*(?:SELECT|DROP|DELETE|UPDATE|INSERT)',  # Multiple statements
    ]
    
    for pattern in dangerous_patterns:
        if re.search(pattern, normalized_query):
            raise SQLSecurityError(
                f"Query contains potentially dangerous operation: {pattern}"
            )
    
    # Check for comment injection attempts
    if '--' in query or '/*' in query or '*/' in query:
        raise SQLSecurityError("Query contains SQL comments which are not allowed")
    
    # Check for common injection patterns
    injection_patterns = [
        r"'\s*OR\s*'?1'?\s*=\s*'?1",  # 'OR 1=1
        r'"\s*OR\s*"?1"?\s*=\s*"?1',  # "OR 1=1
        r'\bUNION\s+(?:ALL\s+)?SELECT\b',  # UNION SELECT
        r"'\s*;",  # Attempting to end statement
        r'"\s*;',  # Attempting to end statement
    ]
    
    for pattern in injection_patterns:
        if re.search(pattern, normalized_query, re.IGNORECASE):
            raise SQLSecurityError(
                f"Query contains potential SQL injection pattern"
            )
    
    return True


def sanitize_value_for_like(value: str) -> str:
    """
    Sanitize a value for use in a LIKE clause by escaping special characters.
    
    Args:
        value: The value to sanitize
        
    Returns:
        str: The sanitized value safe for use in LIKE clauses
    """
    # Escape special LIKE characters
    value = value.replace('\\', '\\\\')  # Escape backslash first
    value = value.replace('%', '\\%')    # Escape percent
    value = value.replace('_', '\\_')    # Escape underscore
    value = value.replace('[', '\\[')    # Escape opening bracket
    
    return value


def build_safe_in_clause(column: str, values: List[Any]) -> Tuple[str, List[Any]]:
    """
    Build a safe IN clause with proper parameterization.
    
    Args:
        column: The column name (will be validated and escaped)
        values: List of values for the IN clause
        
    Returns:
        Tuple[str, List[Any]]: The query fragment and parameters
        
    Example:
        clause, params = build_safe_in_clause("status", ["active", "pending"])
        # Returns: ("[status] IN (?, ?)", ["active", "pending"])
    """
    if not values:
        raise SQLSecurityError("IN clause requires at least one value")
    
    validate_identifier(column, "column")
    escaped_column = escape_identifier(column)
    
    placeholders = ', '.join(['?' for _ in values])
    clause = f"{escaped_column} IN ({placeholders})"
    
    return clause, values


def get_safe_table_list(conn: sqlite3.Connection) -> List[str]:
    """
    Get a list of all tables in the database safely.
    
    Args:
        conn: SQLite connection object
        
    Returns:
        List[str]: List of table names
    """
    cursor = conn.cursor()
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
    )
    return [row[0] for row in cursor.fetchall()]


def check_table_exists(conn: sqlite3.Connection, table_name: str) -> bool:
    """
    Check if a table exists in the database safely.
    
    Args:
        conn: SQLite connection object
        table_name: Name of the table to check
        
    Returns:
        bool: True if table exists, False otherwise
    """
    try:
        validate_identifier(table_name, "table")
    except SQLSecurityError:
        return False
    
    cursor = conn.cursor()
    cursor.execute(
        "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name=?",
        (table_name,)
    )
    return cursor.fetchone()[0] > 0