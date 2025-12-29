# Natural Language SQL Interface

## Project Overview
Build a natural language SQL interface MVP.

**Tech Stack:**
- Frontend: Vite + Vanilla TypeScript (modern dev experience, type safety, zero framework complexity)
- Backend: Python FastAPI + uv (fast dependency management, type safety, auto docs)
- Database: SQLite (portable, zero setup)

**MVP Core Flow:**
1. User drags/drops .json or .csv file → Convert to SQLite table
2. User types "show me users who signed up last week" → AI generates SQL → Execute query → Render table

**Why Vite + TypeScript?**
- Modern dev experience that engineers actually use
- TypeScript adds safety without framework overhead

## V1 Implementation Details

### Architecture Structure

```
app/
    client/
        package.json               # Node dependencies
        vite.config.ts            # Vite configuration
        tsconfig.json             # TypeScript configuration
        src/
            main.ts               # Entry point
            api/
                client.ts         # API client configuration
                endpoints.ts      # API endpoint definitions
            components/
                FileUpload/
                    index.html    # Component template
                    FileUpload.ts # Drag/drop logic
                    styles.css    # Component styling
                TableRenderer/
                    index.html    # Table template
                    TableRenderer.ts # Table generation logic
                    styles.css    # Table styling
                InsightsPanel/
                    index.html    # Insights template
                    InsightsPanel.ts # Auto-insights logic
                    styles.css    # Insights styling
                QueryInput/
                    index.html    # Query input template
                    QueryInput.ts # Natural language input logic
                    styles.css    # Input styling
            utils/
                helpers.ts        # Utility functions
                validators.ts     # Input validation
            types.d.ts            # Global TypeScript type definitions
            styles/
                main.css          # Global styling
                variables.css     # CSS custom properties
        public/
            index.html            # Main HTML template

    server/
        server.py                 # FastAPI app + API routes
        pyproject.toml            # Python dependencies (managed with uv)
        core/
            data_models.py        # Pydantic models (synced with types.d.ts)
            file_processor.py     # File upload → SQLite conversion
            llm_processor.py      # LLM integration (OpenAI/Anthropic)
            sql_processor.py      # SQL generation and execution
            table_renderer.py     # Result formatting
            insights.py           # Auto-insights generation
        tests/
            test_file_processor.py
            test_llm_processor.py
            test_sql_processor.py
        db/
            database.db           # SQLite database file
            schema.sql           # Database schema

ai_docs/
specs/
.claude/
```

## Dependencies and Libraries

### Backend (Python)
```toml
# pyproject.toml
[dependencies]
fastapi = "^0.100.0"           # Web framework with type hints
pydantic = "^2.0.0"            # Data validation and serialization
uvicorn = "^0.23.0"            # ASGI server
python-multipart = "^0.0.6"    # File upload support
sqlite3 = "built-in"           # Database (Python standard library)
openai = "^1.0.0"              # OpenAI API client
anthropic = "^0.25.0"          # Anthropic API client
pandas = "^2.0.0"              # Data processing for CSV/JSON
```

### Frontend (TypeScript)
```json
// package.json
{
  "devDependencies": {
    "vite": "^5.0.0",
    "typescript": "^5.0.0",
    "@types/node": "^20.0.0"
  }
}
```

## Data Models and Type Synchronization

**Important**: All Pydantic models in `server/core/data_models.py` must be kept in sync with TypeScript definitions in `client/src/types.d.ts`. 

### Request/Response Pattern
All API endpoints follow the `...Request` / `...Response` naming convention for clear type safety.

### Core Data Models

```python
# server/core/data_models.py
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime

# File Upload Models
class FileUploadRequest(BaseModel):
    # Handled by FastAPI UploadFile, no request model needed
    pass

class FileUploadResponse(BaseModel):
    table_name: str
    schema: Dict[str, str]  # column_name: data_type
    row_count: int
    sample_data: List[Dict[str, Any]]
    error: Optional[str] = None

# Query Models  
class QueryRequest(BaseModel):
    query: str = Field(..., description="Natural language query")
    llm_provider: Literal["openai", "anthropic"] = "openai"
    table_name: Optional[str] = None  # If querying specific table

class QueryResponse(BaseModel):
    sql: str
    results: List[Dict[str, Any]]
    columns: List[str]
    row_count: int
    execution_time_ms: float
    error: Optional[str] = None

# Database Schema Models
class ColumnInfo(BaseModel):
    name: str
    type: str
    nullable: bool = True
    primary_key: bool = False

class TableSchema(BaseModel):
    name: str
    columns: List[ColumnInfo]
    row_count: int
    created_at: datetime

class DatabaseSchemaRequest(BaseModel):
    pass  # No input needed

class DatabaseSchemaResponse(BaseModel):
    tables: List[TableSchema]
    total_tables: int
    error: Optional[str] = None

# Insights Models
class InsightsRequest(BaseModel):
    table_name: str
    column_names: Optional[List[str]] = None  # If None, analyze all columns

class ColumnInsight(BaseModel):
    column_name: str
    data_type: str
    unique_values: int
    null_count: int
    min_value: Optional[Any] = None
    max_value: Optional[Any] = None
    avg_value: Optional[float] = None
    most_common: Optional[List[Dict[str, Any]]] = None

class InsightsResponse(BaseModel):
    table_name: str
    insights: List[ColumnInsight]
    generated_at: datetime
    error: Optional[str] = None

# Health Check Models
class HealthCheckRequest(BaseModel):
    pass

class HealthCheckResponse(BaseModel):
    status: Literal["ok", "error"]
    database_connected: bool
    tables_count: int
    version: str = "1.0.0"
    uptime_seconds: float
```

### TypeScript Equivalent (app/client/src/types.d.ts)
```typescript
// These must match the Pydantic models exactly

// File Upload Types
interface FileUploadResponse {
  table_name: string;
  schema: Record<string, string>;
  row_count: number;
  sample_data: Record<string, any>[];
  error?: string;
}

// Query Types
interface QueryRequest {
  query: string;
  llm_provider: "openai" | "anthropic";
  table_name?: string;
}

interface QueryResponse {
  sql: string;
  results: Record<string, any>[];
  columns: string[];
  row_count: number;
  execution_time_ms: number;
  error?: string;
}

// Database Schema Types
interface ColumnInfo {
  name: string;
  type: string;
  nullable: boolean;
  primary_key: boolean;
}

interface TableSchema {
  name: string;
  columns: ColumnInfo[];
  row_count: number;
  created_at: string;
}

interface DatabaseSchemaResponse {
  tables: TableSchema[];
  total_tables: number;
  error?: string;
}

// Insights Types
interface InsightsRequest {
  table_name: string;
  column_names?: string[];
}

interface ColumnInsight {
  column_name: string;
  data_type: string;
  unique_values: number;
  null_count: number;
  min_value?: any;
  max_value?: any;
  avg_value?: number;
  most_common?: Record<string, any>[];
}

interface InsightsResponse {
  table_name: string;
  insights: ColumnInsight[];
  generated_at: string;
  error?: string;
}

// Health Check Types
interface HealthCheckResponse {
  status: "ok" | "error";
  database_connected: boolean;
  tables_count: number;
  version: string;
  uptime_seconds: number;
}
```

### Core Backend Methods (Python/FastAPI)

```python
# app/server/server.py
from fastapi import FastAPI, File, UploadFile
from core.data_models import *

@app.post("/api/upload", response_model=FileUploadResponse)
async def upload_file(file: UploadFile = File(...)) -> FileUploadResponse:
    """Upload and convert .json or .csv file to SQLite table"""
    pass

@app.post("/api/query", response_model=QueryResponse)
async def process_natural_language_query(request: QueryRequest) -> QueryResponse:
    """Process natural language query and return SQL results"""
    pass

@app.get("/api/schema", response_model=DatabaseSchemaResponse)
async def get_database_schema() -> DatabaseSchemaResponse:
    """Get current database schema and table information"""
    pass

@app.post("/api/insights", response_model=InsightsResponse)
async def generate_insights(request: InsightsRequest) -> InsightsResponse:
    """Generate statistical insights for table columns"""
    pass

@app.get("/api/health", response_model=HealthCheckResponse)
async def health_check() -> HealthCheckResponse:
    """Health check endpoint with database status"""
    pass

# app/server/core/file_processor.py
def convert_csv_to_sqlite(csv_file, table_name):
    """
    Input: CSV file object, desired table name
    Output: Creates SQLite table, returns schema info
    """
    pass

def convert_json_to_sqlite(json_file, table_name):
    """
    Input: JSON file object (array of objects), desired table name  
    Output: Creates SQLite table, returns schema info
    """
    pass

# app/server/core/llm_processor.py
def generate_sql_with_openai(query_text, schema_info):
    """
    Input: Natural language query, database schema
    Output: Generated SQL string
    """
    pass

def generate_sql_with_anthropic(query_text, schema_info):
    """
    Input: Natural language query, database schema
    Output: Generated SQL string
    """
    pass

# app/server/core/sql_processor.py
def execute_sql_safely(sql_query):
    """
    Input: SQL string
    Output: {"results": [{"id": 1, "name": "John"}], "columns": ["id", "name"], "error": null}
    """
    pass

def get_database_schema():
    """
    Output: {"tables": {"users": {"columns": {"id": "INTEGER", "name": "TEXT", "created_at": "DATETIME"}}}}
    """
    pass
```

### Database Setup (SQLite)
- Dynamic table creation from uploaded files
- Support for .json (array of objects) and .csv files
- Auto-detect column types and create appropriate schema
- File names become table names (sanitized)

### Frontend (Vite + TypeScript)
- Modern build pipeline with hot module replacement
- Type-safe API interactions and data structures
- Modular component architecture

#### Core UI Components

**1. QueryInput Component (Primary Focus)**
```typescript
// Primary interaction area - large, prominent text area
interface QueryInputProps {
  onSubmit: (query: string) => void;
  isLoading: boolean;
  placeholder: string;
}
```
- Large, focused textarea for natural language queries
- Simple "Query" submit button (provider selection handled internally)
- Auto-focus on page load
- Loading state disables input during processing
- Follows Zen design with calm, spacious styling

**2. TableRenderer Component (Results Display)**
```typescript
// Robust table with pagination and state management
interface TableRendererProps {
  data: QueryResponse | null;
  isLoading: boolean;
  isVisible: boolean;
  onToggleVisibility: () => void;
  pageSize: number;
}
```
- **Loading State**: Elegant spinner with "Processing query..." message
- **Results Display**: Clean table with sortable columns
- **Pagination**: Page size options (10, 25, 50, 100 rows)
- **Hide/Show Toggle**: Collapse table to focus on next query
- **Empty State**: Friendly message when no results
- **Error State**: Clear error display with retry option
- **Responsive**: Horizontal scroll for wide tables

**3. FileUpload Component (Secondary)**
- Drag/drop zone for .json/.csv files
- File list showing uploaded tables
- Table schema preview on hover

#### UI Layout Structure
```
┌─────────────────────────────────────┐
│  🎯 Natural Language Query Input    │ ← Primary Focus
│  [Large Textarea - Auto-focused]   │
│  [Query]                           │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│  📊 Query Results [Hide] [Show]     │ ← Toggleable
│  ┌─┬─────────┬─────────┬──────────┐ │
│  │▲│ Name    │ Email   │ Signup   │ │
│  ├─┼─────────┼─────────┼──────────┤ │
│  │ │ John    │ j@ex.com│ 2024-01  │ │
│  │ │ Jane    │ jane@...│ 2024-02  │ │
│  └─┴─────────┴─────────┴──────────┘ │
│  Showing 1-25 of 150 results       │
│  [← Prev] [1][2][3]...[6] [Next →] │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│  📁 File Upload (Collapsible)      │ ← Secondary
│  Drag .csv/.json files here        │
└─────────────────────────────────────┘
```

#### State Management

**Frontend Store Pattern (In-Memory)**
```typescript
// app/client/src/utils/ResultsStore.ts
interface StoredQuery {
  id: string;
  query: string;
  sql: string;
  timestamp: number;
  rowCount: number;
  executionTime: number;
}

class ResultsStore {
  private currentData: QueryResponse | null = null;
  private queryHistory: StoredQuery[] = [];
  
  // Show only the most recent result (top-down flow)
  setCurrentResult(query: string, response: QueryResponse) {
    this.currentData = response;
    
    // Store lightweight history metadata (no actual data)
    const historyItem: StoredQuery = {
      id: crypto.randomUUID(),
      query,
      sql: response.sql,
      timestamp: Date.now(),
      rowCount: response.row_count,
      executionTime: response.execution_time_ms
    };
    
    this.queryHistory.unshift(historyItem); // Add to front
    this.notifyComponents();
  }
  
  getCurrentResult(): QueryResponse | null {
    return this.currentData; // Only show first/most recent
  }
  
  getQueryHistory(): StoredQuery[] {
    return this.queryHistory; // For potential history UI later
  }
  
  clearCurrentResult() {
    this.currentData = null;
    this.notifyComponents();
  }
  
  private notifyComponents() {
    // Native DOM event system for component updates
    document.dispatchEvent(new CustomEvent('results-updated', {
      detail: { hasData: this.currentData !== null }
    }));
  }
}

// Singleton instance
export const resultsStore = new ResultsStore();
```

**Component Integration Pattern**
```typescript
// Components listen for store updates via native DOM events
document.addEventListener('results-updated', (event) => {
  const { hasData } = event.detail;
  // Re-render components based on store state
});
```

**Core State Areas:**
- **Query Results**: Single current result (in-memory only)
- **Query History**: Lightweight metadata for executed queries  
- **UI State**: Loading, visibility, pagination (component-local)
- **File Upload**: Uploaded tables list (component-local)

**Design Philosophy:**
- **Top-down flow**: Only show most recent query result
- **Memory-only**: No persistence, fresh start each session
- **Event-driven**: Components react to store changes via DOM events
- **Lightweight**: Store metadata, not full datasets
- **Simple**: No external state management libraries

### Backend (FastAPI)
- Type-safe request/response models with Pydantic
- Automatic API documentation at `/docs` endpoint
- Async-first for non-blocking LLM API calls
- Built-in validation and serialization
- Modern Python with type hints throughout

## Key Commands

### Setup & Installation
```bash
# Backend setup (Python with uv)
cd app/server
uv install                    # Install Python dependencies
uv run python server.py      # Start FastAPI server (localhost:8000)

# Frontend setup (Node with Vite)
npm create vite@latest app/client -- --template vanilla-ts  # Create Vite project with TypeScript
cd app/client
npm install                   # Install TypeScript + Vite dependencies
npm run dev                   # Start Vite dev server (localhost:5173)
```

### Development Commands
```bash
# Backend development
cd app/server
uv run python server.py      # Start FastAPI with hot reload
uv run pytest               # Run Python tests
uv run python -m pytest tests/ -v  # Verbose test output

# Frontend development  
cd app/client
npm run dev                  # Start Vite with HMR (Hot Module Replacement)
npm run build               # Build for production
npm run preview             # Preview production build
npm run type-check          # TypeScript type checking
```

### Common Development Workflow
```bash
# Terminal 1: Backend
cd app/server && uv run python server.py

# Terminal 2: Frontend  
cd app/client && npm run dev

# Terminal 3: Testing
cd app/server && uv run pytest --watch  # Auto-run tests on changes
```

### Database Commands
```bash
# SQLite database operations (from app/server directory)
cd app/server
sqlite3 db/database.db       # Open SQLite CLI
.tables                      # List all tables
.schema table_name          # Show table schema
.quit                       # Exit SQLite CLI
```

### Frontend-Backend Proxy Configuration

**Vite Proxy Setup (app/client/vite.config.ts):**
```typescript
import { defineConfig } from 'vite'

export default defineConfig({
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false
      }
    }
  }
})
```

**API Client Configuration (app/client/src/api/client.ts):**
```typescript
// Base URL configuration - works in both dev and production
const API_BASE_URL = import.meta.env.DEV 
  ? '/api'  // Proxy to backend in development
  : 'http://localhost:8000/api';  // Direct backend in production

export const apiClient = {
  baseURL: API_BASE_URL,
  // All API calls will automatically use the correct base URL
}
```

**Benefits:**
- **No CORS issues** during development
- **Same-origin requests** from frontend to backend
- **Simplified API calls** - just use `/api/upload`, `/api/query`, etc.
- **Production flexibility** - easy to change backend URL for deployment

### Useful Development URLs
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs (FastAPI auto-generated)
- API Redoc: http://localhost:8000/redoc
- Proxied API calls: http://localhost:5173/api/* → http://localhost:8000/api/*

## Implementation Phases

### Phase 1
- Setup Vite + TypeScript frontend with basic build pipeline
- Setup Python FastAPI backend with uv for fast dependency management
- File upload (drag/drop .json/.csv → SQLite conversion)
- Basic LLM integration (OpenAI/Anthropic APIs)
- Simple SQL generation and execution
- Table rendering with error display


## UI Theme and Design System

### Zen Mindful Design Philosophy
The interface follows a "Zen Mindful" design approach that emphasizes clarity, calm interaction, and subtle beauty:

#### Color Palette
```css
/* Primary Colors */
--zen-primary: #6c757d;      /* Mindful gray */
--zen-secondary: #667eea;    /* Calm blue-purple */
--zen-accent: #764ba2;       /* Deep purple */

/* Neutrals */
--zen-white: #ffffff;
--zen-light-gray: #f5f7fa;
--zen-medium-gray: #e0e0e0;
--zen-dark-gray: #495057;
--zen-charcoal: #2c3e50;

/* Gradients */
--zen-bg-gradient: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
--zen-accent-gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
```

#### Typography
```css
/* Font Stack */
font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;

/* Scale */
--zen-text-xs: 12px;    /* Labels, captions */
--zen-text-sm: 14px;    /* Body text, buttons */
--zen-text-md: 16px;    /* Alerts, emphasis */
--zen-text-lg: 18px;    /* Section headers */
--zen-text-xl: 28px;    /* Page title */

/* Weights */
--zen-weight-light: 300;
--zen-weight-normal: 400;
--zen-weight-medium: 500;
```

#### Spacing and Layout
```css
/* Consistent spacing scale */
--zen-space-xs: 8px;
--zen-space-sm: 12px;
--zen-space-md: 16px;
--zen-space-lg: 20px;
--zen-space-xl: 24px;
--zen-space-2xl: 30px;
--zen-space-3xl: 40px;

/* Border radius */
--zen-radius-sm: 8px;    /* Small elements */
--zen-radius-md: 12px;   /* Buttons, inputs */
--zen-radius-lg: 16px;   /* Cards, panels */
--zen-radius-xl: 24px;   /* Main container */
```

#### Component Styling Patterns

**Containers & Cards:**
- Semi-transparent white backgrounds with backdrop blur
- Soft drop shadows: `0 20px 60px rgba(0, 0, 0, 0.1)`
- Rounded corners using consistent radius scale
- Subtle breathing animation on main containers

**Interactive Elements:**
- Hover lift effect: `transform: translateY(-2px)`
- Ripple effect on buttons using ::before pseudo-elements
- Smooth transitions: `transition: all 0.3s ease`
- Focus states with colored box-shadows

**Visual Hierarchy:**
- Gentle animations using `fadeInUp` keyframes
- Staggered animation delays (0.2s, 0.4s, 0.6s, 0.8s)
- Floating orb backgrounds for ambient depth
- Progressive disclosure with opacity and transforms

#### Animation Standards
```css
/* Standard easing */
--zen-ease: cubic-bezier(0.175, 0.885, 0.32, 1.275);
--zen-ease-simple: ease;

/* Animation durations */
--zen-duration-fast: 0.3s;
--zen-duration-normal: 0.5s;
--zen-duration-slow: 1s;

/* Signature animations */
@keyframes breathe {
    0%, 100% { transform: translateY(0) scale(1); }
    50% { transform: translateY(-5px) scale(1.01); }
}

@keyframes fadeInUp {
    from { opacity: 0; transform: translateY(20px); }
    to { opacity: 1; transform: translateY(0); }
}
```

This design system ensures the SQL interface feels calm, professional, and approachable while maintaining modern aesthetic standards.
