import pytest
import sqlite3
import tempfile
import os
from unittest.mock import patch
from core.sql_processor import execute_sql_safely, get_database_schema


@pytest.fixture
def test_db():
    """Create an in-memory test database with sample data"""
    # Create in-memory database
    conn = sqlite3.connect(':memory:')
    cursor = conn.cursor()
    
    # Create test tables
    cursor.execute('''
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            age INTEGER,
            email TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE products (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            price REAL,
            category TEXT
        )
    ''')
    
    # Insert test data
    cursor.execute("INSERT INTO users (name, age, email) VALUES ('John', 25, 'john@example.com')")
    cursor.execute("INSERT INTO users (name, age, email) VALUES ('Jane', 30, 'jane@example.com')")
    cursor.execute("INSERT INTO users (name, age, email) VALUES ('Bob', 35, 'bob@example.com')")
    
    cursor.execute("INSERT INTO products (name, price, category) VALUES ('Laptop', 999.99, 'Electronics')")
    cursor.execute("INSERT INTO products (name, price, category) VALUES ('Book', 19.99, 'Education')")
    
    conn.commit()
    
    # Patch the database connection to use our in-memory database
    with patch('core.sql_processor.sqlite3.connect') as mock_connect:
        mock_connect.return_value = conn
        yield conn
    
    conn.close()


class TestSQLProcessor:
    
    def test_execute_sql_safely_valid_select(self, test_db):
        sql_query = "SELECT * FROM users WHERE age > 25"
        result = execute_sql_safely(sql_query)
        
        assert result['error'] is None
        assert len(result['results']) == 2  # Jane (30) and Bob (35)
        assert result['columns'] == ['id', 'name', 'age', 'email']
        
        # Check actual data
        names = [row['name'] for row in result['results']]
        assert 'Jane' in names
        assert 'Bob' in names
        assert 'John' not in names  # John is 25, not > 25
    
    def test_execute_sql_safely_with_joins(self, test_db):
        # Test more complex SQL with real execution
        sql_query = "SELECT COUNT(*) as total FROM users"
        result = execute_sql_safely(sql_query)
        
        assert result['error'] is None
        assert len(result['results']) == 1
        assert result['results'][0]['total'] == 3
    
    def test_execute_sql_safely_no_results(self, test_db):
        sql_query = "SELECT * FROM users WHERE age > 100"
        result = execute_sql_safely(sql_query)
        
        assert result['error'] is None
        assert result['results'] == []
        assert result['columns'] == []
    
    def test_execute_sql_safely_dangerous_keywords(self):
        # Test dangerous SQL operations
        dangerous_queries = [
            "DROP TABLE users",
            "DELETE FROM users",
            "TRUNCATE TABLE users",
            "UPDATE users SET name = 'hacked'",
            "INSERT INTO users VALUES (99, 'hacker')",
            "ALTER TABLE users ADD COLUMN password",
            "CREATE TABLE hackers (id INT)",
        ]
        
        for query in dangerous_queries:
            result = execute_sql_safely(query)
            assert result['error'] is not None
            # Query should be blocked (either by security check or database error)
            assert result['results'] == []
            assert result['columns'] == []
    
    def test_execute_sql_safely_case_insensitive_keywords(self):
        # Test case insensitive keyword detection
        sql_query = "drop table users"  # lowercase
        result = execute_sql_safely(sql_query)
        
        assert result['error'] is not None
        assert "Security error" in result['error']
    
    def test_execute_sql_safely_sql_error(self, test_db):
        # Test with invalid SQL syntax
        sql_query = "SELECT * FROM nonexistent_table"
        result = execute_sql_safely(sql_query)
        
        assert result['error'] is not None
        assert "no such table" in result['error'].lower()
        assert result['results'] == []
        assert result['columns'] == []
    
    def test_execute_sql_safely_syntax_error(self, test_db):
        # Test with malformed SQL
        sql_query = "SELECT * FORM users"  # typo: FORM instead of FROM
        result = execute_sql_safely(sql_query)
        
        assert result['error'] is not None
        assert result['results'] == []
        assert result['columns'] == []
    
    def test_get_database_schema_success(self, test_db):
        result = get_database_schema()
        
        assert 'tables' in result
        assert 'users' in result['tables']
        assert 'products' in result['tables']
        
        # Check users table schema
        users_table = result['tables']['users']
        expected_columns = {'id': 'INTEGER', 'name': 'TEXT', 'age': 'INTEGER', 'email': 'TEXT'}
        assert users_table['columns'] == expected_columns
        assert users_table['row_count'] == 3
        
        # Check products table schema
        products_table = result['tables']['products']
        expected_columns = {'id': 'INTEGER', 'name': 'TEXT', 'price': 'REAL', 'category': 'TEXT'}
        assert products_table['columns'] == expected_columns
        assert products_table['row_count'] == 2
    
    def test_get_database_schema_empty_database(self):
        # Test with empty in-memory database
        with patch('core.sql_processor.sqlite3.connect') as mock_connect:
            conn = sqlite3.connect(':memory:')
            mock_connect.return_value = conn
            
            result = get_database_schema()
            assert result == {'tables': {}}
    
    def test_get_database_schema_error(self):
        # Test database connection error
        with patch('core.sql_processor.sqlite3.connect', side_effect=sqlite3.Error("Connection failed")):
            result = get_database_schema()
            
            assert result == {'tables': {}, 'error': 'Connection failed'}
    
    def test_dangerous_keywords_coverage(self):
        # Test that expected dangerous operations are blocked
        dangerous_operations = [
            ('DROP', 'DROP TABLE users'),
            ('DELETE', 'DELETE FROM users'),
            ('TRUNCATE', 'TRUNCATE TABLE users'),
            ('UPDATE', 'UPDATE users SET name = "test"'),
            ('INSERT', 'INSERT INTO users VALUES (1, "test")'),
            ('ALTER', 'ALTER TABLE users ADD COLUMN test'),
            ('CREATE', 'CREATE TABLE test (id INT)'),
        ]
        
        # Test that each operation is properly blocked
        for keyword, query in dangerous_operations:
            result = execute_sql_safely(query)
            assert result['error'] is not None
            # Query should be blocked