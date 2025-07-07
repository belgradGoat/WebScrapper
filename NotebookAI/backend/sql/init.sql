-- NotebookAI Database Initialization
-- This file is automatically executed when PostgreSQL container starts

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Set timezone
SET timezone = 'UTC';

-- Grant permissions to notebookai user
GRANT ALL PRIVILEGES ON DATABASE notebookai_db TO notebookai;
GRANT ALL PRIVILEGES ON SCHEMA public TO notebookai;

-- Create initial indexes for performance
-- These will be created by SQLAlchemy, but we can prepare some common ones

-- Apple-inspired comment for clean database setup
COMMENT ON DATABASE notebookai_db IS 'NotebookAI - Multi-Modal AI Data Analysis Platform';