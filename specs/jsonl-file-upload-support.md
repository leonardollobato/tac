# Feature: JSONL File Upload Support

## Feature Description
Add support for uploading JSONL (JSON Lines) files to the Natural Language SQL Interface application. JSONL files contain one JSON object per line, making them efficient for streaming and processing large datasets. This feature will enable users to upload .jsonl files alongside the existing .csv and .json file formats, automatically parsing the entire file to detect all possible fields (including nested objects and arrays), flattening the structure using a configurable delimiter, and creating a single table in the SQLite database.

## User Story
As a data analyst
I want to upload JSONL files to the Natural Language SQL Interface
So that I can query data stored in JSONL format using natural language without manually converting it to CSV or JSON format first

## Problem Statement
Currently, the application only supports CSV and JSON array file uploads. Many data sources and APIs export data in JSONL format (one JSON object per line), which is a standard format for streaming and large datasets. Users with JSONL data must manually convert their files to supported formats before using the application, creating friction in the workflow. Additionally, when JSON/JSONL files contain nested objects or arrays, users need a way to access this nested data in SQL queries through a flattened table structure.

## Solution Statement
Implement JSONL file processing that:
1. Accepts .jsonl file uploads through the existing upload interface
2. Reads through the entire JSONL file to discover all possible fields across all records
3. Flattens nested objects using a configurable delimiter (default: "__") to create column names
4. Handles arrays by creating indexed columns with a configurable list index notation (e.g., "_0", "_1")
5. Stores delimiter configuration in a constants file for easy updates
6. Creates a single SQLite table from the flattened data structure
7. Follows existing security patterns for SQL injection prevention
8. Updates the UI to inform users about JSONL support
9. Uses only Python standard library (no new external dependencies)

## Relevant Files
Use these files to implement the feature:

- **app/server/core/file_processor.py** (lines 1-174)
  - Contains existing CSV and JSON file processing logic
  - Defines `sanitize_table_name()` function for table name validation
  - Implements `convert_csv_to_sqlite()` and `convert_json_to_sqlite()` functions
  - Will need new `convert_jsonl_to_sqlite()` function following same pattern
  - Will need helper functions for flattening nested structures

- **app/server/server.py** (lines 72-109)
  - Contains `/api/upload` endpoint that validates file types
  - Currently only accepts `.csv` and `.json` extensions
  - Needs to add `.jsonl` to accepted file types
  - Routes file processing based on extension

- **app/server/core/sql_security.py** (lines 1-276)
  - Provides security utilities for SQL injection prevention
  - Contains `validate_identifier()` and `escape_identifier()` functions
  - Used by file processors to ensure safe table/column names
  - Existing functions will be used for JSONL column name validation

- **app/client/index.html** (lines 79-81)
  - Contains file upload UI with accepted file types
  - File input currently accepts `.csv,.json`
  - Needs to add `.jsonl` to accepted types
  - Drop zone text needs update to mention JSONL support

- **app/client/src/main.ts** (lines 93-106)
  - Handles file upload client-side logic
  - Calls `api.uploadFile()` for file processing
  - No changes needed, but should verify file extension handling

- **app/server/tests/core/test_file_processor.py** (lines 1-164)
  - Contains test cases for CSV and JSON file processing
  - Needs new test class or test methods for JSONL processing
  - Should test nested objects, arrays, field discovery, and edge cases

### New Files

- **app/server/core/constants.py**
  - New file to store configuration constants
  - Will contain `NESTED_FIELD_DELIMITER` (default: "__")
  - Will contain `LIST_INDEX_DELIMITER` (default: "_")
  - Allows easy updates to delimiter configuration

- **app/server/tests/assets/test_events.jsonl**
  - Sample JSONL file with nested objects for testing
  - Will contain user events with nested user data and metadata

- **app/server/tests/assets/test_products_nested.jsonl**
  - Sample JSONL file with arrays for testing
  - Will contain products with nested attributes and tag arrays

- **app/server/tests/assets/simple.jsonl**
  - Simple JSONL file with flat objects for basic testing
  - Will contain simple records without nesting

## Implementation Plan

### Phase 1: Foundation
Create the constants configuration file and implement core flattening utilities that will be used by the JSONL processor. This includes:
- Creating `constants.py` with delimiter configurations
- Implementing field discovery logic to scan all JSONL records
- Building flattening functions for nested objects and arrays
- Ensuring all generated column names pass SQL security validation

### Phase 2: Core Implementation
Build the JSONL processing function following the same pattern as existing CSV and JSON processors:
- Implement `convert_jsonl_to_sqlite()` function in `file_processor.py`
- Parse JSONL line by line using Python's standard JSON library
- Discover all possible fields by scanning the entire file
- Flatten records using the delimiter configuration
- Convert flattened data to pandas DataFrame for SQLite insertion
- Return schema, row count, and sample data in the same format as existing processors

### Phase 3: Integration
Integrate JSONL support into the existing upload workflow and update the user interface:
- Update server endpoint to accept `.jsonl` files
- Update client HTML and file input to accept `.jsonl` files
- Update UI text to inform users about JSONL support
- Create comprehensive test cases with various JSONL structures
- Create sample JSONL test files for validation

## Step by Step Tasks

### Step 1: Create Constants Configuration File
- Create `app/server/core/constants.py` file
- Define `NESTED_FIELD_DELIMITER = "__"` constant
- Define `LIST_INDEX_DELIMITER = "_"` constant
- Add module docstring explaining delimiter usage and examples
- Document how delimiters are used for flattening (e.g., `user__name`, `tags_0`)

### Step 2: Implement Field Discovery and Flattening Functions
- In `app/server/core/file_processor.py`, import constants
- Add `discover_all_fields(records: List[Dict]) -> Set[str]` function
  - Iterate through all records to find all possible field paths
  - Handle nested objects by exploring recursively
  - Handle arrays by determining maximum length across all records
  - Return set of all flattened field names
- Add `flatten_record(record: Dict, delimiter: str, list_delimiter: str) -> Dict[str, Any]` function
  - Recursively flatten nested objects using delimiter
  - Flatten arrays using list_delimiter and index
  - Handle null/None values appropriately
  - Return flat dictionary with all values at root level
- Write comprehensive docstrings for both functions with examples
- Add type hints for all parameters and return values

### Step 3: Implement JSONL to SQLite Conversion Function
- In `app/server/core/file_processor.py`, create `convert_jsonl_to_sqlite(jsonl_content: bytes, table_name: str) -> Dict[str, Any]` function
- Sanitize table name using existing `sanitize_table_name()` function
- Parse JSONL content line by line using Python's `json` module
- Collect all records in a list
- Use `discover_all_fields()` to find all possible columns
- Flatten all records using `flatten_record()` function
- Create pandas DataFrame from flattened records
- Ensure all discovered fields exist as columns (fill missing with None)
- Clean column names using same pattern as CSV/JSON processors
- Connect to SQLite database and write table using `df.to_sql()`
- Retrieve schema, sample data, and row count using existing secure query patterns
- Return result dictionary matching format of existing processors
- Add comprehensive error handling with descriptive messages

### Step 4: Create Test JSONL Files
- Create `app/server/tests/assets/simple.jsonl` with flat records (3-4 records)
  - Simple user records without nesting: id, name, email, age
- Create `app/server/tests/assets/test_events.jsonl` with nested objects (5-6 records)
  - Event records with nested user object: `{event: "login", user: {id: 1, name: "John"}, timestamp: "..."}`
  - Should flatten to columns like: `event`, `user__id`, `user__name`, `timestamp`
- Create `app/server/tests/assets/test_products_nested.jsonl` with arrays (4-5 records)
  - Product records with tag arrays: `{id: 1, name: "Product", tags: ["tag1", "tag2"]}`
  - Should flatten to columns like: `id`, `name`, `tags_0`, `tags_1`
- Ensure varied field presence across records to test field discovery

### Step 5: Write Comprehensive JSONL Tests
- In `app/server/tests/core/test_file_processor.py`, add new test methods
- Add `test_convert_jsonl_to_sqlite_simple()` test
  - Load simple.jsonl and convert to SQLite
  - Verify table creation, schema, row count
  - Verify sample data matches expected records
- Add `test_convert_jsonl_to_sqlite_nested_objects()` test
  - Load test_events.jsonl and convert
  - Verify nested fields are flattened with `__` delimiter
  - Verify flattened column names in schema (e.g., `user__id`, `user__name`)
  - Verify values are correctly extracted from nested structure
- Add `test_convert_jsonl_to_sqlite_with_arrays()` test
  - Load test_products_nested.jsonl and convert
  - Verify array fields are flattened with index notation (e.g., `tags_0`, `tags_1`)
  - Verify all array indices are captured based on maximum array length
- Add `test_convert_jsonl_to_sqlite_field_discovery()` test
  - Create JSONL with varying fields across records
  - Verify all fields from all records are discovered
  - Verify records with missing fields have None/NULL values
- Add `test_convert_jsonl_to_sqlite_invalid()` test
  - Test with invalid JSONL (malformed JSON lines)
  - Verify appropriate error handling and messages
- Add `test_convert_jsonl_to_sqlite_empty()` test
  - Test with empty JSONL file
  - Verify appropriate error handling
- Add `test_flatten_record()` unit test
  - Test flattening function directly with various nested structures
  - Verify delimiter usage and correct output
- Add `test_discover_all_fields()` unit test
  - Test field discovery with varying record structures
  - Verify all fields are found

### Step 6: Update Server Endpoint to Accept JSONL
- In `app/server/server.py`, locate the `/api/upload` endpoint (line 73-109)
- Update file type validation to include `.jsonl` extension
  - Change line 77 from: `if not file.filename.endswith(('.csv', '.json')):`
  - To: `if not file.filename.endswith(('.csv', '.json', '.jsonl')):`
- Update error message to mention JSONL: `"Only .csv, .json, and .jsonl files are supported"`
- Add JSONL processing logic after line 89:
  ```python
  elif file.filename.endswith('.jsonl'):
      result = convert_jsonl_to_sqlite(content, table_name)
  ```
- Import `convert_jsonl_to_sqlite` at the top of the file with other imports
- Verify error handling covers JSONL processing errors

### Step 7: Update Client UI for JSONL Support
- In `app/client/index.html`, update the drop zone text (line 80)
  - Change from: `<p>Drag and drop .csv or .json files here</p>`
  - To: `<p>Drag and drop .csv, .json, or .jsonl files here</p>`
- Update the file input accept attribute (line 81)
  - Change from: `accept=".csv,.json"`
  - To: `accept=".csv,.json,.jsonl"`
- Update README.md to document JSONL support:
  - Update line 8 to mention `.jsonl` files
  - Update line 86 to mention `.jsonl` in the upload instructions
  - Add section explaining JSONL format and nested field flattening

### Step 8: Run Tests and Validate Implementation
- Run server tests: `cd app/server && uv run pytest tests/core/test_file_processor.py -v`
- Verify all JSONL tests pass
- Run full test suite: `cd app/server && uv run pytest -v`
- Verify no regressions in existing CSV and JSON tests
- Test manually by starting the application and uploading each test JSONL file
- Verify UI shows JSONL as accepted file type
- Verify successful table creation from JSONL uploads
- Verify flattened columns appear correctly in the table schema display
- Verify natural language queries work against JSONL-created tables

### Step 9: End-to-End Validation
- Start the application: `./scripts/start.sh`
- Open browser to http://localhost:5173
- Test JSONL upload workflow:
  - Click "Upload Data" button
  - Drag and drop `simple.jsonl` test file
  - Verify success message and table creation
  - Verify column names and data in Available Tables section
  - Run natural language query against the table
  - Verify results are correct
- Test nested JSONL upload:
  - Upload `test_events.jsonl`
  - Verify nested fields are flattened (look for `__` in column names)
  - Query the nested fields (e.g., "show me all user names")
- Test array JSONL upload:
  - Upload `test_products_nested.jsonl`
  - Verify array indices appear as separate columns (e.g., `tags_0`, `tags_1`)
  - Query the array fields
- Verify existing CSV and JSON uploads still work correctly
- Run all Validation Commands to ensure zero regressions

## Testing Strategy

### Unit Tests
- **Test field discovery function**: Verify all fields are discovered across multiple records with varying structures
- **Test flattening function**: Test with nested objects at multiple levels, arrays of different sizes, mixed types
- **Test delimiter configuration**: Verify constants are used correctly for flattening
- **Test column name sanitization**: Ensure flattened names pass SQL security validation
- **Test empty/invalid JSONL**: Verify appropriate error handling for malformed input

### Integration Tests
- **Test simple JSONL conversion**: Flat records without nesting should work like JSON arrays
- **Test nested object JSONL**: Multi-level nested objects should flatten correctly with delimiters
- **Test array JSONL**: Arrays should create indexed columns for each element
- **Test field discovery across records**: Fields present in some records but not others should be handled
- **Test JSONL upload endpoint**: Full workflow from file upload to table creation
- **Test query execution**: Natural language queries should work on JSONL-created tables

### Edge Cases
- **Empty JSONL file**: Should return appropriate error message
- **Malformed JSON lines**: Should handle parsing errors gracefully
- **Inconsistent nesting depth**: Some records deeply nested, others flat
- **Large arrays**: Arrays with many elements should create appropriate number of columns
- **Missing fields**: Records missing fields present in other records should have NULL values
- **Special characters in keys**: Nested keys with special characters should be sanitized
- **Very deep nesting**: Objects nested 5+ levels deep should flatten correctly
- **Empty objects/arrays**: Should handle empty nested structures
- **Mixed data types**: Same field with different types across records
- **Unicode in field names**: Non-ASCII characters in JSON keys should be handled

## Acceptance Criteria
1. Users can upload .jsonl files through the existing upload modal
2. JSONL files are parsed line by line to extract all records
3. All fields across all records are discovered and become table columns
4. Nested objects are flattened using `__` delimiter (e.g., `user__name`)
5. Arrays are flattened using `_` delimiter with indices (e.g., `tags_0`, `tags_1`)
6. Delimiter configuration is stored in `constants.py` and can be easily updated
7. Generated column names pass SQL security validation
8. Single SQLite table is created from JSONL data
9. Table schema, row count, and sample data are returned to client
10. UI displays JSONL as supported file format in upload modal
11. File input accepts `.jsonl` extension
12. No new external dependencies are added (uses Python standard library)
13. All existing CSV and JSON functionality remains unchanged
14. Comprehensive tests cover simple, nested, and array scenarios
15. All tests pass with zero regressions
16. Natural language queries work correctly on JSONL-created tables
17. README documentation updated to reflect JSONL support

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

- `cd app/server && uv run pytest tests/core/test_file_processor.py::TestFileProcessor::test_convert_jsonl_to_sqlite_simple -v` - Test simple JSONL conversion
- `cd app/server && uv run pytest tests/core/test_file_processor.py::TestFileProcessor::test_convert_jsonl_to_sqlite_nested_objects -v` - Test nested object flattening
- `cd app/server && uv run pytest tests/core/test_file_processor.py::TestFileProcessor::test_convert_jsonl_to_sqlite_with_arrays -v` - Test array flattening
- `cd app/server && uv run pytest tests/core/test_file_processor.py::TestFileProcessor::test_convert_jsonl_to_sqlite_field_discovery -v` - Test field discovery across records
- `cd app/server && uv run pytest tests/core/test_file_processor.py::TestFileProcessor::test_flatten_record -v` - Test flattening utility function
- `cd app/server && uv run pytest tests/core/test_file_processor.py::TestFileProcessor::test_discover_all_fields -v` - Test field discovery utility function
- `cd app/server && uv run pytest tests/core/test_file_processor.py -v` - Run all file processor tests including existing CSV/JSON tests
- `cd app/server && uv run pytest tests/test_sql_injection.py -v` - Verify SQL security is not compromised
- `cd app/server && uv run pytest -v` - Run full test suite to ensure zero regressions
- `./scripts/start.sh` - Start application and manually test JSONL upload workflow (Ctrl+C to stop)

## Notes

### Delimiter Configuration
The delimiters are configurable via `constants.py`:
- `NESTED_FIELD_DELIMITER = "__"`: Used for nested objects (e.g., `user.name` → `user__name`)
- `LIST_INDEX_DELIMITER = "_"`: Used for array indices (e.g., `tags[0]` → `tags_0`)

### Flattening Examples
**Nested Objects:**
```json
{"user": {"id": 1, "name": "John", "address": {"city": "NYC"}}}
```
Flattens to columns: `user__id`, `user__name`, `user__address__city`

**Arrays:**
```json
{"product": "Widget", "tags": ["electronics", "gadget", "new"]}
```
Flattens to columns: `product`, `tags_0`, `tags_1`, `tags_2`

**Mixed:**
```json
{"order": {"id": 1, "items": [{"name": "A"}, {"name": "B"}]}}
```
Flattens to columns: `order__id`, `order__items_0__name`, `order__items_1__name`

### Field Discovery Strategy
The implementation scans ALL records in the JSONL file before creating the table to ensure all possible fields are discovered. This is important because JSONL records may have varying schemas. Records missing certain fields will have NULL values for those columns in SQLite.

### Performance Considerations
For very large JSONL files, the implementation loads all records into memory for field discovery and pandas DataFrame creation. This follows the same pattern as existing CSV and JSON processors. For production use with very large files, streaming and chunking could be added in the future.

### Security
All flattened column names are validated using the existing `validate_identifier()` function from `sql_security.py` to prevent SQL injection. Column names with invalid characters are sanitized using the same logic as CSV column name cleaning.

### No New Dependencies
This implementation uses only Python standard library modules (`json`, `io`) along with existing dependencies (`pandas`, `sqlite3`). No new packages need to be installed via `uv add`.

### Future Enhancements
- Support for deeply nested arrays of objects
- Configurable maximum nesting depth for flattening
- Option to skip flattening and store JSON as TEXT columns
- Streaming parser for very large JSONL files
- Column type inference improvements for nested data
