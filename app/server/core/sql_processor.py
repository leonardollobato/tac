import sqlite3
import re
from typing import Dict, Any, List
from .sql_security import (
    execute_query_safely, 
    validate_sql_query, 
    SQLSecurityError,
    check_table_exists
)

def execute_sql_safely(sql_query: str) -> Dict[str, Any]:
    """
    Execute SQL query with safety checks
    """
    try:
        # Validate the SQL query for dangerous operations
        validate_sql_query(sql_query)
        
        # Connect to database
        conn = sqlite3.connect("db/database.db")
        conn.row_factory = sqlite3.Row  # Enable column access by name
        
        # Execute query safely
        # Note: Since this is a user-provided complete SQL query,
        # we can't use parameterization. The validate_sql_query
        # function provides protection against dangerous operations.
        cursor = conn.cursor()
        cursor.execute(sql_query)
        
        # Get results
        rows = cursor.fetchall()
        
        # Convert rows to dictionaries
        results = []
        columns = []
        
        if rows:
            columns = list(rows[0].keys())
            for row in rows:
                results.append(dict(row))
        
        conn.close()
        
        return {
            'results': results,
            'columns': columns,
            'error': None
        }
    
    except SQLSecurityError as e:
        return {
            'results': [],
            'columns': [],
            'error': f"Security error: {str(e)}"
        }
    except Exception as e:
        return {
            'results': [],
            'columns': [],
            'error': str(e)
        }

def get_database_schema() -> Dict[str, Any]:
    """
    Get complete database schema information
    """
    try:
        conn = sqlite3.connect("db/database.db")
        cursor = conn.cursor()
        
        # Get all tables safely
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        schema = {'tables': {}}
        
        for table in tables:
            table_name = table[0]
            
            # Skip system tables
            if table_name.startswith('sqlite_'):
                continue
            
            try:
                # Get columns for each table using safe query execution
                cursor_info = execute_query_safely(
                    conn,
                    "PRAGMA table_info({table})",
                    identifier_params={'table': table_name}
                )
                columns_info = cursor_info.fetchall()
                
                columns = {}
                for col in columns_info:
                    columns[col[1]] = col[2]  # column_name: data_type
                
                # Get row count safely
                cursor_count = execute_query_safely(
                    conn,
                    "SELECT COUNT(*) FROM {table}",
                    identifier_params={'table': table_name}
                )
                row_count = cursor_count.fetchone()[0]
                
                schema['tables'][table_name] = {
                    'columns': columns,
                    'row_count': row_count
                }
                
            except SQLSecurityError:
                # Skip tables with invalid names
                continue
        
        conn.close()
        
        return schema
        
    except Exception as e:
        return {'tables': {}, 'error': str(e)}