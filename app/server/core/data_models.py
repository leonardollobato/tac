from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime

# File Upload Models
class FileUploadRequest(BaseModel):
    # Handled by FastAPI UploadFile, no request model needed
    pass

class FileUploadResponse(BaseModel):
    table_name: str
    table_schema: Dict[str, str]  # column_name: data_type
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