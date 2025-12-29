"""
Comprehensive tests for SQL injection protection
"""

import pytest
import sqlite3
import tempfile
import os
from unittest.mock import patch, MagicMock
from core.sql_security import (
    validate_identifier,
    escape_identifier,
    execute_query_safely,
    validate_sql_query,
    sanitize_value_for_like,
    build_safe_in_clause,
    check_table_exists,
    SQLSecurityError
)
from core.sql_processor import execute_sql_safely, get_database_schema
from core.file_processor import sanitize_table_name
from core.insights import generate_insights


@pytest.fixture
def test_db():
    """Create a test database with sample data"""
    db_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    db_file.close()
    
    conn = sqlite3.connect(db_file.name)
    cursor = conn.cursor()
    
    # Create test tables
    cursor.execute('''
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT,
            age INTEGER
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE products (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            price REAL
        )
    ''')
    
    # Insert test data
    cursor.execute("INSERT INTO users (name, email, age) VALUES (?, ?, ?)",
                   ('Alice', 'alice@example.com', 30))
    cursor.execute("INSERT INTO users (name, email, age) VALUES (?, ?, ?)",
                   ('Bob', 'bob@example.com', 25))
    cursor.execute("INSERT INTO products (name, price) VALUES (?, ?)",
                   ('Widget', 19.99))
    
    conn.commit()
    conn.close()
    
    yield db_file.name
    
    # Cleanup
    os.unlink(db_file.name)


class TestSQLSecurityModule:
    """Test the SQL security utility functions"""
    
    def test_validate_identifier_valid(self):
        """Test validation of valid identifiers"""
        assert validate_identifier("users", "table")
        assert validate_identifier("user_id", "column")
        assert validate_identifier("_temp_table", "table")
        assert validate_identifier("column_123", "column")
        assert validate_identifier("first_name", "column")
    
    def test_validate_identifier_invalid(self):
        """Test validation of invalid identifiers"""
        with pytest.raises(SQLSecurityError):
            validate_identifier("", "table")
        
        with pytest.raises(SQLSecurityError):
            validate_identifier("users'; DROP TABLE users; --", "table")
        
        with pytest.raises(SQLSecurityError):
            validate_identifier("123_table", "table")  # starts with number
        
        with pytest.raises(SQLSecurityError):
            validate_identifier("user-name", "column")  # contains hyphen
        
        with pytest.raises(SQLSecurityError):
            validate_identifier("SELECT", "table")  # SQL keyword
    
    def test_escape_identifier(self):
        """Test identifier escaping"""
        assert escape_identifier("users") == "[users]"
        assert escape_identifier("user_table") == "[user_table]"
        
        # Test escaping of closing bracket
        with pytest.raises(SQLSecurityError):
            escape_identifier("table]name")  # Invalid character
    
    def test_execute_query_safely(self, test_db):
        """Test safe query execution"""
        conn = sqlite3.connect(test_db)
        
        # Test with identifier parameters
        cursor = execute_query_safely(
            conn,
            "SELECT * FROM {table} WHERE id = ?",
            params=(1,),
            identifier_params={'table': 'users'}
        )
        result = cursor.fetchone()
        assert result is not None
        
        # Test without value parameters
        cursor = execute_query_safely(
            conn,
            "SELECT COUNT(*) FROM {table}",
            identifier_params={'table': 'products'}
        )
        count = cursor.fetchone()[0]
        assert count == 1
        
        conn.close()
    
    def test_execute_query_safely_injection_attempt(self, test_db):
        """Test that injection attempts are blocked"""
        conn = sqlite3.connect(test_db)
        
        # Test injection through identifier
        with pytest.raises(SQLSecurityError):
            execute_query_safely(
                conn,
                "SELECT * FROM {table}",
                identifier_params={'table': "users; DROP TABLE users; --"}
            )
        
        conn.close()
    
    def test_validate_sql_query(self):
        """Test SQL query validation"""
        # Valid queries
        assert validate_sql_query("SELECT * FROM users")
        assert validate_sql_query("SELECT name, email FROM users WHERE age > 18")
        
        # Invalid queries - dangerous operations
        with pytest.raises(SQLSecurityError):
            validate_sql_query("DROP TABLE users")
        
        with pytest.raises(SQLSecurityError):
            validate_sql_query("DELETE FROM users")
        
        with pytest.raises(SQLSecurityError):
            validate_sql_query("SELECT * FROM users; DROP TABLE users")
        
        # SQL injection patterns
        with pytest.raises(SQLSecurityError):
            validate_sql_query("SELECT * FROM users WHERE name = '' OR '1'='1'")
        
        with pytest.raises(SQLSecurityError):
            validate_sql_query("SELECT * FROM users -- comment")
    
    def test_sanitize_value_for_like(self):
        """Test LIKE clause sanitization"""
        assert sanitize_value_for_like("test") == "test"
        assert sanitize_value_for_like("test%") == "test\\%"
        assert sanitize_value_for_like("test_name") == "test\\_name"
        assert sanitize_value_for_like("test[") == "test\\["
    
    def test_build_safe_in_clause(self):
        """Test safe IN clause building"""
        clause, params = build_safe_in_clause("status", ["active", "pending"])
        assert clause == "[status] IN (?, ?)"
        assert params == ["active", "pending"]
        
        # Test with invalid column name
        with pytest.raises(SQLSecurityError):
            build_safe_in_clause("status; DROP TABLE", ["active"])
    
    def test_check_table_exists(self, test_db):
        """Test table existence check"""
        conn = sqlite3.connect(test_db)
        
        assert check_table_exists(conn, "users")
        assert check_table_exists(conn, "products")
        assert not check_table_exists(conn, "nonexistent_table")
        
        # Test with injection attempt
        assert not check_table_exists(conn, "users; DROP TABLE users")
        
        conn.close()


class TestSQLProcessorSecurity:
    """Test SQL processor with security enhancements"""
    
    @patch('core.sql_processor.sqlite3.connect')
    def test_execute_sql_safely_blocks_dangerous_queries(self, mock_connect):
        """Test that dangerous SQL queries are blocked"""
        # Test DROP statement
        result = execute_sql_safely("DROP TABLE users")
        assert result['error'] is not None
        assert "Security error" in result['error']
        
        # Test DELETE statement
        result = execute_sql_safely("DELETE FROM users WHERE id = 1")
        assert result['error'] is not None
        assert "Security error" in result['error']
        
        # Test multiple statements
        result = execute_sql_safely("SELECT * FROM users; DROP TABLE users")
        assert result['error'] is not None
        assert "Security error" in result['error']
    
    @patch('core.sql_processor.sqlite3.connect')
    def test_execute_sql_safely_allows_select(self, mock_connect):
        """Test that safe SELECT queries are allowed"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = []
        
        result = execute_sql_safely("SELECT * FROM users WHERE id = 1")
        assert result['error'] is None
        mock_cursor.execute.assert_called_once()


class TestFileProcessorSecurity:
    """Test file processor with security enhancements"""
    
    def test_sanitize_table_name_injection_attempts(self):
        """Test that table name sanitization prevents injection"""
        # Test various injection attempts
        assert sanitize_table_name("users'; DROP TABLE users; --") != "users'; DROP TABLE users; --"
        assert sanitize_table_name("users.csv") == "users"
        assert sanitize_table_name("my-table-name") == "my_table_name"
        assert sanitize_table_name("123table") == "_123table"
        
        # Test that sanitized names are valid identifiers
        for malicious_name in [
            "'; DROP TABLE users; --",
            "../../../etc/passwd",
            "users UNION SELECT * FROM passwords",
            "users/*comment*/data"
        ]:
            sanitized = sanitize_table_name(malicious_name)
            # This should not raise an error
            validate_identifier(sanitized, "table")


class TestInsightsSecurity:
    """Test insights module with security enhancements"""
    
    @patch('core.insights.sqlite3.connect')
    def test_generate_insights_validates_table_name(self, mock_connect):
        """Test that table names are validated"""
        with pytest.raises(Exception) as exc_info:
            generate_insights("users'; DROP TABLE users; --")
        assert "Invalid" in str(exc_info.value)
    
    @patch('core.insights.sqlite3.connect')
    def test_generate_insights_validates_column_names(self, mock_connect):
        """Test that column names are validated"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        with pytest.raises(Exception) as exc_info:
            generate_insights("users", ["name", "'; DROP TABLE users; --"])
        assert "Invalid column name" in str(exc_info.value)


class TestEndToEndSQLInjection:
    """End-to-end tests for SQL injection prevention"""
    
    def test_malicious_table_names(self, test_db):
        """Test handling of malicious table names"""
        malicious_names = [
            "users'; DROP TABLE users; --",
            "users' OR '1'='1",
            "users UNION SELECT * FROM sqlite_master",
            "'; DELETE FROM users WHERE '1'='1"
        ]
        
        for name in malicious_names:
            # File processor should sanitize
            sanitized = sanitize_table_name(name)
            # Check that dangerous characters are removed
            assert "'" not in sanitized
            assert ";" not in sanitized
            # Verify it's a valid identifier
            validate_identifier(sanitized, "table")
    
    def test_malicious_sql_queries(self):
        """Test handling of malicious SQL queries"""
        malicious_queries = [
            "SELECT * FROM users; DROP TABLE users",
            "SELECT * FROM users WHERE '1'='1' OR '1'='1'",
            "SELECT * FROM users UNION SELECT * FROM passwords",
            "SELECT * FROM users WHERE id = 1; DELETE FROM users",
        ]
        
        for query in malicious_queries:
            result = execute_sql_safely(query)
            assert result['error'] is not None
            assert result['results'] == []
    
    def test_sql_comment_injection(self):
        """Test that SQL comments are blocked"""
        queries_with_comments = [
            "SELECT * FROM users -- DROP TABLE users",
            "SELECT * FROM users /* DROP TABLE users */",
            "SELECT * FROM users WHERE id = 1 --' OR 1=1"
        ]
        
        for query in queries_with_comments:
            result = execute_sql_safely(query)
            assert result['error'] is not None


def test_integration_upload_malicious_filename(test_db):
    """Test that malicious filenames are handled safely during upload"""
    from core.file_processor import convert_csv_to_sqlite
    
    # Create a simple CSV content
    csv_content = b"name,age\nAlice,30\nBob,25"
    
    # Try with malicious filename
    malicious_name = "data'; DROP TABLE users; --.csv"
    result = convert_csv_to_sqlite(csv_content, malicious_name)
    
    # The table should be created with a sanitized name
    assert result['table_name'] != malicious_name
    assert "'" not in result['table_name']
    assert ";" not in result['table_name']
    # Verify it's a valid identifier
    validate_identifier(result['table_name'], "table")