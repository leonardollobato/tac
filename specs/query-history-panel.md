# Feature: Query History Side Panel

## Feature Description
A new collapsible side panel that displays a chronological list of all completed queries, allowing users to quickly revisit and re-execute previous queries. Each query will have an auto-generated descriptive name created by an LLM based on the query content. The panel will be positioned on the right side of the interface and can be toggled via a button next to the existing "Upload Data" button. When a user clicks on a query in the history, the main query input will be populated with that query and the results will be displayed, effectively refocusing the main panel on the selected query.

## User Story
As a data analyst
I want to see a history of all my previous queries with descriptive names
So that I can quickly revisit and re-run queries without having to remember or retype them

## Problem Statement
Currently, users lose track of their previous queries once they run a new one. There's no way to revisit past queries without manually copying them somewhere else. This makes iterative data exploration difficult, especially when users want to refine queries or compare results from different queries. Additionally, remembering the exact phrasing of complex natural language queries can be challenging.

## Solution Statement
Implement a persistent query history panel that stores all executed queries in the database with auto-generated descriptive names. The panel will provide a chronological list (newest first) of all queries with their generated names, execution timestamps, and status indicators. Users can click any query to instantly reload it into the main interface. This solution leverages the existing LLM infrastructure to generate meaningful names for each query, making the history easy to scan and understand at a glance.

## Relevant Files
Use these files to implement the feature:

**Server-side files:**
- `app/server/server.py` - Add new endpoints for query history management
- `app/server/core/data_models.py` - Add new Pydantic models for query history
- `app/server/core/sql_processor.py` - Extend to handle query history table operations
- `app/server/core/llm_processor.py` - Add function to generate query names

**Client-side files:**
- `app/client/src/main.ts` - Add side panel UI logic and event handlers
- `app/client/src/api/client.ts` - Add API methods for query history
- `app/client/src/types.d.ts` - Add TypeScript interfaces for query history
- `app/client/index.html` - Add HTML structure for side panel
- `app/client/styles.css` - Add styles for side panel and animations

### New Files
- `app/server/core/query_history.py` - New module for query history database operations
- `app/client/src/queryHistory.ts` - New module for query history UI management

## Implementation Plan
### Phase 1: Foundation
Set up the database infrastructure and core data models needed to store query history. This includes creating the query history table, defining the data models, and implementing basic database operations.

### Phase 2: Core Implementation
Implement the server-side API endpoints for saving and retrieving query history, integrate LLM name generation, and modify the existing query endpoint to save history. Then build the client-side UI components for the side panel.

### Phase 3: Integration
Connect all components together, ensure proper state management between the main query interface and the history panel, add animations and polish the user experience, and thoroughly test the feature.

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Create Database Schema
- Create a new SQLite table `query_history` with columns: id (INTEGER PRIMARY KEY), query_text (TEXT), generated_name (TEXT), sql_query (TEXT), status (TEXT), error_message (TEXT), created_at (TIMESTAMP), row_count (INTEGER)
- Implement migration logic in server startup to create table if it doesn't exist
- Add indexes on created_at for efficient ordering

### Add Data Models
- Create `QueryHistoryItem` Pydantic model in `data_models.py` with all fields from the database schema
- Create `QueryHistoryListResponse` model for returning paginated history
- Create `QueryNameGenerationRequest` model for LLM name generation
- Add `save_to_history` boolean field to existing `QueryRequest` model (default True)

### Implement Query History Module
- Create `app/server/core/query_history.py` with functions: save_query, get_query_history, get_query_by_id, delete_query
- Implement proper SQL injection protection using existing sql_security patterns
- Add error handling and logging
- Write unit tests for all database operations

### Add LLM Name Generation
- Add `generate_query_name` function to `llm_processor.py` that takes query text and returns a short descriptive name
- Use a specific prompt that asks for a 3-5 word summary of the query intent
- Implement fallback to use first few words of query if LLM fails
- Cache generated names to avoid regenerating for identical queries

### Modify Query Endpoint
- Update `/api/query` endpoint in `server.py` to save queries to history after successful execution
- Generate query name asynchronously to not block the main query response
- Store both successful and failed queries with appropriate status
- Ensure security validations are maintained

### Add Query History Endpoints
- Add `GET /api/query-history` endpoint with pagination support (limit, offset)
- Add `GET /api/query-history/{id}` endpoint to get specific query details
- Add `DELETE /api/query-history/{id}` endpoint to remove queries
- Add proper error handling and validation

### Create Query History API Client
- Add methods to `api/client.ts`: getQueryHistory, getQueryById, deleteQuery
- Add proper TypeScript types matching the Pydantic models
- Implement error handling with user-friendly messages
- Add loading states for async operations

### Build Side Panel HTML Structure
- Add panel container div with class `query-history-panel` to index.html
- Add toggle button next to "Upload Data" button with icon and text "Show History"
- Create panel header with title and close button
- Add scrollable container for query list items
- Ensure proper accessibility with ARIA attributes

### Create Query History UI Module
- Create `app/client/src/queryHistory.ts` with functions to manage panel state
- Implement `initializeQueryHistory` to set up event listeners
- Add `loadQueryHistory` to fetch and display queries
- Implement `displayQueryItem` to render individual history items
- Add `selectQuery` to load query into main interface

### Style the Side Panel
- Add CSS for sliding panel animation from right side
- Style query items as clickable cards with hover effects
- Add status indicators (success/error) with appropriate colors
- Implement responsive design for smaller screens
- Add loading skeleton animation while fetching history

### Implement Panel Interactions
- Add toggle functionality with smooth slide animation
- Store panel state in localStorage for persistence
- Add click handlers for query items to load into main interface
- Implement delete functionality with confirmation
- Add keyboard navigation support (Escape to close, arrow keys to navigate)

### Add Real-time Updates
- Update history panel when new queries are executed
- Show loading state while query name is being generated
- Update query item with generated name once available
- Implement optimistic updates for better UX

### Write Integration Tests
- Test query history saving with various query types
- Test LLM name generation with edge cases
- Test panel toggle and state persistence
- Test query selection and main interface updates
- Test concurrent query execution and history updates

### Performance Optimization
- Implement virtual scrolling if history grows large
- Add database cleanup for old queries (configurable retention)
- Optimize query history endpoint with proper pagination
- Add caching for frequently accessed queries

### Final Polish
- Add empty state message when no query history exists
- Implement search/filter functionality for query history
- Add export functionality for query history
- Ensure all error states have appropriate user feedback
- Run all validation commands to ensure zero regressions

## Testing Strategy
### Unit Tests
- Test query history database operations (CRUD operations)
- Test LLM name generation with mocked API responses
- Test query history API endpoints with various payloads
- Test client-side state management and UI updates
- Test error handling for all edge cases

### Integration Tests
- Test full flow from query execution to history display
- Test panel interactions with main query interface
- Test concurrent users accessing query history
- Test database migrations and schema updates
- Test LLM failover and fallback name generation

### Edge Cases
- Empty query text handling
- Very long queries that need truncation
- LLM API failures during name generation
- Database connection failures during history operations
- Malformed SQL queries in history
- Special characters in query text
- Timezone handling for timestamps
- Panel state when switching between different browser tabs

## Acceptance Criteria
- Query history panel can be toggled open/closed via button next to "Upload Data"
- All executed queries are saved to the database with timestamps
- Each query has an auto-generated descriptive name visible in the panel
- Queries are displayed in reverse chronological order (newest first)
- Clicking a query in the history loads it into the main query input
- Query results are displayed when a historical query is selected
- Failed queries are marked with error status in the history
- Users can delete individual queries from history
- Panel state persists across page refreshes
- Performance remains smooth with hundreds of queries in history
- All existing functionality continues to work without regression

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

- `cd app/server && uv run pytest` - Run server tests to validate the feature works with zero regressions
- `cd app/server && uv run pytest tests/core/test_query_history.py -v` - Run specific query history tests
- `cd app/server && uv run python -m pytest tests/test_sql_injection.py -v` - Ensure SQL injection protection still works
- `cd scripts && ./start.sh` - Start the application and manually test:
  - Execute multiple queries and verify they appear in history
  - Toggle panel open/closed multiple times
  - Click on historical queries and verify they load correctly
  - Test query name generation quality
  - Delete queries and verify they're removed
  - Refresh page and verify panel state persists
  - Test with both OpenAI and Anthropic API keys
- `cd app/client && npm run build` - Ensure client builds without errors
- `cd app/server && uv run python test_manual_injection.py` - Test security with manual injection attempts

## Notes
- Consider implementing query history export functionality in a future iteration
- The 3-5 word name generation might need tuning based on user feedback
- Future enhancement could include query categorization or tagging
- Consider adding query execution metrics (duration, rows affected) to history display
- The query history retention policy should be configurable via environment variables
- Consider implementing query templates feature building on top of history
- May need to implement pagination on the client side if users have extensive history
- The LLM name generation could be enhanced with few-shot examples for consistency