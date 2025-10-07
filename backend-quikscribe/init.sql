-- Initialize QuikScribe Database
-- This script runs when the PostgreSQL container starts

-- Create extensions if they don't exist
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create additional schemas if needed
CREATE SCHEMA IF NOT EXISTS quikscribe;

-- Set search path
SET search_path TO quikscribe, public;

-- You can add initial data or additional setup here
-- For now, the database will be created empty and Alembic will handle migrations
