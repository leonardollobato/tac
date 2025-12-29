# Bug: SQL Injection Vulnerabilities

## Bug Description
The application has multiple SQL injection vulnerabilities where user input and table/column names are being concatenated directly into SQL queries using f-strings and string interpolation. This allows potential attackers to inject malicious SQL code through:
- Natural language queries that get converted to SQL
- Table names from uploaded files
- Column names in insights generation
- Direct SQL execution without parameterization

Expected behavior: All SQL queries should use parameterized queries (prepared statements) to prevent SQL injection.
Actual behavior: SQL statements are constructed using string concatenation/interpolation, making them vulnerable to injection attacks.

## Problem Statement
The codebase directly concatenates user input and dynamic values into SQL queries without proper parameterization or escaping. This occurs in multiple files:
- `sql_processor.py`: Direct execution of generated SQL queries
- `file_processor.py`: String interpolation with table names in PRAGMA and SELECT statements
- `insights.py`: String interpolation with table and column names
- `server.py`: String interpolation in DROP TABLE statement

## Solution Statement
Replace all string concatenation/interpolation in SQL queries with parameterized queries where possible. For DDL statements and identifiers (table/column names) that cannot be parameterized, implement strict validation and use proper escaping/quoting mechanisms. Additionally, implement a centralized SQL execution layer with built-in protection.

## Steps to Reproduce
1. Start the application with `./scripts/start.sh`
2. Upload a CSV file with a malicious name like `users'; DROP TABLE users; --`
3. Or send a natural language query that generates SQL with injection: "Show all data from users WHERE 1=1; DROP TABLE users; --"
4. The malicious SQL will be executed directly without protection

## Root Cause Analysis
The root cause is the use of string formatting (f-strings) and direct concatenation to build SQL queries instead of using parameterized queries. This happens because:
1. The developers assumed that basic keyword blocking (DROP, DELETE, etc.) was sufficient protection
2. Table and column names were trusted without validation since they come from uploaded files
3. SQLite's parameter binding doesn't support identifiers (table/column names), leading to string interpolation usage
4. No centralized SQL execution layer with built-in protection mechanisms

## Relevant Files
Use these files to fix the bug:

- `app/server/core/sql_processor.py` - Contains execute_sql_safely() which directly executes SQL queries without parameterization
- `app/server/core/file_processor.py` - Uses f-string interpolation for table names in multiple cursor.execute() calls
- `app/server/core/insights.py` - Uses f-string interpolation for both table and column names in SQL queries
- `app/server/server.py` - Contains a DROP TABLE statement with f-string interpolation in the delete_table endpoint

### New Files
- `app/server/core/sql_security.py` - New file to implement centralized SQL security utilities including identifier validation and safe query execution

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### 1. Create SQL Security Module
Create a new module with utilities for SQL security:
- Implement identifier validation functions for table and column names
- Create a safe query executor that uses parameterization where possible
- Add proper escaping for identifiers that cannot be parameterized
- Include comprehensive input validation

### 2. Fix SQL Processor Module
Update `sql_processor.py` to use parameterized queries:
- Replace direct cursor.execute(sql_query) with a safe execution method
- Update get_database_schema() to use proper identifier escaping
- Ensure all queries use parameter binding where possible

### 3. Fix File Processor Module
Update `file_processor.py` to prevent injection through table names:
- Use the new SQL security utilities for all queries
- Replace f-string interpolation with safe identifier quoting
- Ensure table names are properly validated before use

### 4. Fix Insights Module
Update `insights.py` to prevent injection through table and column names:
- Replace all f-string SQL queries with safe alternatives
- Use parameter binding for values and safe quoting for identifiers
- Validate all table and column names before use

### 5. Fix Server Module
Update `server.py` to fix the DELETE endpoint vulnerability:
- Replace the f-string DROP TABLE with safe execution
- Improve table name validation beyond just alphanumeric check
- Use the centralized SQL security utilities

### 6. Add Comprehensive Tests
Create tests to verify SQL injection protection:
- Test malicious table names during file upload
- Test SQL injection attempts in natural language queries
- Test injection attempts through column names in insights
- Verify all endpoints are protected

### 7. Update Documentation
Update the README and code comments:
- Document the SQL security measures in place
- Add examples of how to safely execute queries
- Include security best practices for future development

## Validation Commands
Execute every command to validate the bug is fixed with zero regressions.

- `cd app/server && uv run pytest -v` - Run all server tests to ensure no regressions
- `cd app/server && uv run pytest tests/test_sql_injection.py -v` - Run specific SQL injection tests
- `cd app/server && uv run python -m test_manual_injection` - Manual test script to verify injection attempts are blocked
- `./scripts/start.sh` - Start the application and manually test:
  - Upload a file named `test'; DROP TABLE test; --.csv`
  - Try natural language query: "Show users WHERE 1=1; DELETE FROM users; --"
  - Verify malicious SQL is blocked but legitimate queries still work

## Notes
- SQLite doesn't support parameterized identifiers (table/column names), so we must use proper escaping and validation
- The pandas `to_sql()` method is already safe from injection as it handles escaping internally
- We'll use the `sqlite3.Row` factory which is already in place for safe column access
- The solution maintains backward compatibility while adding security
- Consider using `uv add sqlparse` if advanced SQL parsing is needed for validation