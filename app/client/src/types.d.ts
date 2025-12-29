// These must match the Pydantic models exactly

// File Upload Types
interface FileUploadResponse {
  table_name: string;
  table_schema: Record<string, string>;
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