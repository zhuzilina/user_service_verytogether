-- PostgreSQL database initialization script
-- This script runs when the database container starts for the first time

-- Create additional extensions if needed
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";

-- Set up timezone
SET timezone = 'UTC';

-- Create additional schemas or users if needed
-- (This is a placeholder for any custom database setup)

-- Grant necessary permissions
GRANT ALL PRIVILEGES ON DATABASE user_service_db TO postgres;
