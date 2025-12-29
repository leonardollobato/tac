# Chore: Replace Server Print Statements with Python Logging

## Chore Description
Replace all print statements in the server code with proper Python logging using appropriate log levels. The logging should preserve the exact same log output and ensure all output is written to standard out. This will provide better control over log verbosity, formatting, and allow for future extensibility.

## Relevant Files
Use these files to resolve the chore:

- `app/server/server.py` - Main FastAPI application with 19 print statements that need to be replaced
  - Line 78: Success message for file upload
  - Lines 81-82: Error messages for file upload failures
  - Line 116: Success message for query processing
  - Lines 119-120: Error messages for query processing failures
  - Line 158: Success message for schema retrieval
  - Lines 161-162: Error messages for schema retrieval failures
  - Line 179: Success message for insights generation
  - Lines 182-183: Error messages for insights generation failures
  - Line 210: Success message for health check
  - Lines 213-214: Error messages for health check failures
  - Line 248: Success message for table deletion
  - Lines 253-254: Error messages for table deletion failures

- `app/server/main.py` - Simple main module with 1 print statement
  - Line 2: Hello message that needs to be replaced with logging

## Step by Step Tasks

### Step 1: Set up logging configuration in server.py
- Import the logging module at the top of server.py
- Configure the logger with appropriate format that preserves the existing message structure
- Set up a stream handler to ensure output goes to stdout
- Set the default log level to INFO

### Step 2: Replace print statements in server.py
- Create a logger instance for the server module
- Replace all print statements with appropriate logging levels:
  - Use logger.info() for success messages (lines 78, 116, 158, 179, 210, 248)
  - Use logger.error() for error messages (lines 81, 82, 119, 120, 161, 162, 182, 183, 213, 214, 253, 254)
- Preserve the exact same message format with [SUCCESS] and [ERROR] prefixes
- For traceback printing, use logger.error() with exc_info parameter or format_exc()

### Step 3: Replace print statement in main.py
- Import the logging module
- Create a logger instance for the main module
- Replace the print statement on line 2 with logger.info()
- Preserve the exact message "Hello from server!"

### Step 4: Run validation commands
- Execute pytest to ensure no regressions
- Start the server to verify logging output appears correctly on stdout

## Validation Commands
Execute every command to validate the chore is complete with zero regressions.

- `cd app/server && uv run pytest` - Run server tests to validate the chore is complete with zero regressions
- `cd app/server && uv run python server.py` - Start the server and verify all log messages appear correctly on stdout
- `cd app/server && uv run python main.py` - Run main.py to verify the hello message is logged correctly

## Notes
- The logging configuration should use a simple format that matches the existing output style
- All log output must go to stdout (not stderr) to maintain compatibility
- The [SUCCESS] and [ERROR] prefixes in the existing messages should be preserved
- Consider using %(asctime)s in the format for timestamps if needed in the future
- The logging level should be set to INFO by default to show both info and error messages