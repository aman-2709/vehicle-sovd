-- ============================================================================
-- SOVD Command WebApp - Initial Database Schema
-- Database: PostgreSQL 15+
-- Created: 2025-10-28
-- Description: Creates all tables, indexes, constraints, and seed data for
--              the Service-Oriented Vehicle Diagnostics (SOVD) platform
-- ============================================================================

-- ============================================================================
-- Section 1: Extensions and Setup
-- ============================================================================

-- Note: gen_random_uuid() is built-in from PostgreSQL 13+, but we include
-- pgcrypto extension for backward compatibility if needed
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- ============================================================================
-- Section 2: Table Creation
-- ============================================================================
-- Tables are created in dependency order to satisfy foreign key constraints:
-- 1. users, vehicles (no dependencies)
-- 2. commands (depends on users and vehicles)
-- 3. responses (depends on commands)
-- 4. sessions (depends on users)
-- 5. audit_logs (depends on users, vehicles, commands)
-- ============================================================================

-- ----------------------------------------------------------------------------
-- Table: users
-- Description: User account information and authentication credentials
-- Purpose: Stores user authentication data with role-based access control (RBAC)
-- ----------------------------------------------------------------------------
CREATE TABLE users (
    user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL CHECK (role IN ('engineer', 'admin')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

COMMENT ON TABLE users IS 'User accounts with authentication credentials and RBAC';
COMMENT ON COLUMN users.role IS 'User role for RBAC: engineer (basic access) or admin (full access)';
COMMENT ON COLUMN users.password_hash IS 'Bcrypt-hashed password for secure authentication';

-- ----------------------------------------------------------------------------
-- Table: vehicles
-- Description: Connected vehicle registry with real-time connection tracking
-- Purpose: Tracks all vehicles registered in the SOVD platform
-- ----------------------------------------------------------------------------
CREATE TABLE vehicles (
    vehicle_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    vin VARCHAR(17) NOT NULL UNIQUE,
    make VARCHAR(100) NOT NULL,
    model VARCHAR(100) NOT NULL,
    year INTEGER NOT NULL,
    connection_status VARCHAR(20) NOT NULL CHECK (connection_status IN ('connected', 'disconnected', 'error')),
    last_seen_at TIMESTAMP WITH TIME ZONE,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

COMMENT ON TABLE vehicles IS 'Registry of all vehicles in the SOVD platform with connection tracking';
COMMENT ON COLUMN vehicles.vin IS 'Vehicle Identification Number (17 characters, ISO 3779 standard)';
COMMENT ON COLUMN vehicles.connection_status IS 'Real-time connection status for monitoring';
COMMENT ON COLUMN vehicles.metadata IS 'JSONB field for flexible vehicle-specific attributes (e.g., firmware version, capabilities)';

-- ----------------------------------------------------------------------------
-- Table: commands
-- Description: SOVD command execution records with status tracking
-- Purpose: Tracks all commands submitted by users to vehicles
-- ----------------------------------------------------------------------------
CREATE TABLE commands (
    command_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    vehicle_id UUID NOT NULL REFERENCES vehicles(vehicle_id) ON DELETE CASCADE,
    command_name VARCHAR(100) NOT NULL,
    command_params JSONB NOT NULL DEFAULT '{}',
    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'in_progress', 'completed', 'failed')),
    error_message TEXT,
    submitted_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    completed_at TIMESTAMP WITH TIME ZONE
);

COMMENT ON TABLE commands IS 'Command execution records with lifecycle tracking';
COMMENT ON COLUMN commands.command_name IS 'SOVD command identifier (e.g., "read_dtc", "clear_dtc")';
COMMENT ON COLUMN commands.command_params IS 'JSONB field for command-specific parameters';
COMMENT ON COLUMN commands.status IS 'Command execution lifecycle status';
COMMENT ON CONSTRAINT commands_user_id_fkey ON commands IS 'CASCADE delete: remove commands when user is deleted';
COMMENT ON CONSTRAINT commands_vehicle_id_fkey ON commands IS 'CASCADE delete: remove commands when vehicle is deleted';

-- ----------------------------------------------------------------------------
-- Table: responses
-- Description: Streaming command responses with sequence tracking
-- Purpose: Stores ordered response chunks from vehicle command execution
-- ----------------------------------------------------------------------------
CREATE TABLE responses (
    response_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    command_id UUID NOT NULL REFERENCES commands(command_id) ON DELETE CASCADE,
    response_payload JSONB NOT NULL,
    sequence_number INTEGER NOT NULL,
    is_final BOOLEAN NOT NULL DEFAULT false,
    received_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

COMMENT ON TABLE responses IS 'Streaming command responses stored in sequence order';
COMMENT ON COLUMN responses.response_payload IS 'JSONB field for streaming response data chunks';
COMMENT ON COLUMN responses.sequence_number IS 'Sequence order for reassembling streaming responses';
COMMENT ON COLUMN responses.is_final IS 'Flag indicating the final response chunk in the stream';
COMMENT ON CONSTRAINT responses_command_id_fkey ON responses IS 'CASCADE delete: remove responses when command is deleted';

-- ----------------------------------------------------------------------------
-- Table: sessions
-- Description: User authentication sessions with JWT refresh token storage
-- Purpose: Manages user session lifecycle and refresh token rotation
-- ----------------------------------------------------------------------------
CREATE TABLE sessions (
    session_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    refresh_token VARCHAR(500) NOT NULL UNIQUE,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

COMMENT ON TABLE sessions IS 'User authentication sessions with JWT refresh tokens';
COMMENT ON COLUMN sessions.refresh_token IS 'JWT refresh token for session renewal (must be unique)';
COMMENT ON COLUMN sessions.expires_at IS 'Token expiration timestamp for cleanup and security';
COMMENT ON CONSTRAINT sessions_user_id_fkey ON sessions IS 'CASCADE delete: remove sessions when user is deleted';

-- ----------------------------------------------------------------------------
-- Table: audit_logs
-- Description: Comprehensive audit trail of all system events
-- Purpose: Records all user actions, system events, and security-relevant operations
-- ----------------------------------------------------------------------------
CREATE TABLE audit_logs (
    log_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(user_id) ON DELETE SET NULL,
    vehicle_id UUID REFERENCES vehicles(vehicle_id) ON DELETE SET NULL,
    command_id UUID REFERENCES commands(command_id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    entity_id UUID,
    details JSONB DEFAULT '{}',
    ip_address VARCHAR(45),
    user_agent TEXT,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT now()
);

COMMENT ON TABLE audit_logs IS 'Comprehensive audit trail preserving history even when entities are deleted';
COMMENT ON COLUMN audit_logs.user_id IS 'Nullable FK to preserve audit trail when user is deleted';
COMMENT ON COLUMN audit_logs.action IS 'Action type (e.g., "user.login", "command.submit", "vehicle.connect")';
COMMENT ON COLUMN audit_logs.entity_type IS 'Type of entity being audited (e.g., "user", "command", "vehicle")';
COMMENT ON COLUMN audit_logs.details IS 'JSONB field for event-specific information';
COMMENT ON COLUMN audit_logs.ip_address IS 'Client IP address (supports both IPv4 and IPv6 with VARCHAR(45))';
COMMENT ON CONSTRAINT audit_logs_user_id_fkey ON audit_logs IS 'SET NULL: preserve audit log even when user is deleted';
COMMENT ON CONSTRAINT audit_logs_vehicle_id_fkey ON audit_logs IS 'SET NULL: preserve audit log even when vehicle is deleted';
COMMENT ON CONSTRAINT audit_logs_command_id_fkey ON audit_logs IS 'SET NULL: preserve audit log even when command is deleted';

-- ============================================================================
-- Section 3: Index Creation
-- ============================================================================
-- Total indexes: 21 (exceeds minimum requirement of 15)
-- Indexes are grouped by table for clarity
-- Naming convention: idx_{table}_{column(s)} or unq_{table}_{column}
-- ============================================================================

-- ----------------------------------------------------------------------------
-- Indexes: users table (3 indexes)
-- ----------------------------------------------------------------------------

-- Unique indexes on username and email are automatically created by UNIQUE constraints
-- but we explicitly name them for consistency
CREATE UNIQUE INDEX idx_users_username ON users(username);
CREATE UNIQUE INDEX idx_users_email ON users(email);

-- Index for RBAC filtering (e.g., SELECT * FROM users WHERE role = 'admin')
CREATE INDEX idx_users_role ON users(role);

-- ----------------------------------------------------------------------------
-- Indexes: vehicles table (3 indexes)
-- ----------------------------------------------------------------------------

-- Unique index on VIN is automatically created but explicitly named
CREATE UNIQUE INDEX idx_vehicles_vin ON vehicles(vin);

-- Index for filtering connected/disconnected vehicles (common monitoring query)
CREATE INDEX idx_vehicles_connection_status ON vehicles(connection_status);

-- Index for time-based queries (e.g., find vehicles not seen in last 24 hours)
CREATE INDEX idx_vehicles_last_seen_at ON vehicles(last_seen_at);

-- ----------------------------------------------------------------------------
-- Indexes: commands table (5 indexes)
-- ----------------------------------------------------------------------------

-- Index for retrieving all commands submitted by a specific user
CREATE INDEX idx_commands_user_id ON commands(user_id);

-- Index for retrieving all commands sent to a specific vehicle
CREATE INDEX idx_commands_vehicle_id ON commands(vehicle_id);

-- Index for filtering commands by execution status (e.g., find all pending commands)
CREATE INDEX idx_commands_status ON commands(status);

-- Index for time-based queries (e.g., recent commands, oldest pending commands)
CREATE INDEX idx_commands_submitted_at ON commands(submitted_at);

-- Composite index for common query pattern: vehicle's commands filtered by status
-- Example: SELECT * FROM commands WHERE vehicle_id = ? AND status = 'pending'
CREATE INDEX idx_commands_vehicle_id_status ON commands(vehicle_id, status);

-- ----------------------------------------------------------------------------
-- Indexes: responses table (2 indexes)
-- ----------------------------------------------------------------------------

-- Index for retrieving all responses for a specific command
CREATE INDEX idx_responses_command_id ON responses(command_id);

-- Composite index for ordered retrieval of command responses
-- Example: SELECT * FROM responses WHERE command_id = ? ORDER BY sequence_number
CREATE INDEX idx_responses_command_id_sequence ON responses(command_id, sequence_number);

-- ----------------------------------------------------------------------------
-- Indexes: sessions table (3 indexes)
-- ----------------------------------------------------------------------------

-- Unique index on refresh_token is automatically created but explicitly named
CREATE UNIQUE INDEX idx_sessions_refresh_token ON sessions(refresh_token);

-- Index for retrieving all sessions for a specific user (session management)
CREATE INDEX idx_sessions_user_id ON sessions(user_id);

-- Index for cleanup queries (e.g., delete expired sessions)
-- Example: DELETE FROM sessions WHERE expires_at < now()
CREATE INDEX idx_sessions_expires_at ON sessions(expires_at);

-- ----------------------------------------------------------------------------
-- Indexes: audit_logs table (5 indexes)
-- ----------------------------------------------------------------------------

-- Index for retrieving complete audit trail for a specific user
CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);

-- Index for retrieving all events related to a specific vehicle
CREATE INDEX idx_audit_logs_vehicle_id ON audit_logs(vehicle_id);

-- Index for retrieving all events related to a specific command
CREATE INDEX idx_audit_logs_command_id ON audit_logs(command_id);

-- Index for filtering logs by action type (e.g., all login events)
CREATE INDEX idx_audit_logs_action ON audit_logs(action);

-- Index for time-based queries (e.g., recent events, events in date range)
CREATE INDEX idx_audit_logs_timestamp ON audit_logs(timestamp);

-- ============================================================================
-- Section 4: Seed Data Insertion
-- ============================================================================
-- Seed data for development and testing:
-- - 2 users (admin, engineer) with bcrypt-hashed passwords
-- - 2 vehicles (Tesla Model 3, BMW X5) with different connection states
-- Using hardcoded UUIDs for predictable testing
-- ============================================================================

-- ----------------------------------------------------------------------------
-- Seed Data: Users
-- ----------------------------------------------------------------------------

-- Admin user with full system access
INSERT INTO users (
    user_id,
    username,
    email,
    password_hash,
    role,
    created_at,
    updated_at
) VALUES (
    '00000000-0000-0000-0000-000000000001',
    'admin',
    'admin@sovd.example.com',
    '$2b$12$gKiBBRQgNbcpUiSj7P9w.OGyKPljbkwoMfuyiRTcJbLM5qerXCT0u', -- password: admin123
    'admin',
    now(),
    now()
);

-- Engineer user with basic access
INSERT INTO users (
    user_id,
    username,
    email,
    password_hash,
    role,
    created_at,
    updated_at
) VALUES (
    '00000000-0000-0000-0000-000000000002',
    'engineer',
    'engineer@sovd.example.com',
    '$2b$12$LkFSe5of6fWoK4RNgxR4POndNPHnVTlbxEyV2edtBPbqNkcQFBoGy', -- password: engineer123
    'engineer',
    now(),
    now()
);

-- ----------------------------------------------------------------------------
-- Seed Data: Vehicles
-- ----------------------------------------------------------------------------

-- Vehicle 1: Connected Tesla Model 3 (for testing connected state)
INSERT INTO vehicles (
    vehicle_id,
    vin,
    make,
    model,
    year,
    connection_status,
    last_seen_at,
    metadata,
    created_at
) VALUES (
    '00000000-0000-0000-0000-000000000101',
    'TESTVIN0000000001',
    'Tesla',
    'Model 3',
    2023,
    'connected',
    now(),
    '{"firmware_version": "2023.44.1", "battery_capacity": "75kWh", "autopilot": true}'::jsonb,
    now()
);

-- Vehicle 2: Disconnected BMW X5 (for testing disconnected state)
INSERT INTO vehicles (
    vehicle_id,
    vin,
    make,
    model,
    year,
    connection_status,
    last_seen_at,
    metadata,
    created_at
) VALUES (
    '00000000-0000-0000-0000-000000000102',
    'TESTVIN0000000002',
    'BMW',
    'X5',
    2022,
    'disconnected',
    now() - INTERVAL '2 hours',
    '{"firmware_version": "v8.5.2", "fuel_type": "hybrid", "drive_type": "xDrive"}'::jsonb,
    now()
);

-- ============================================================================
-- Schema Creation Complete
-- ============================================================================

-- Verification queries (commented out - can be uncommented for manual testing)
-- SELECT COUNT(*) AS table_count FROM information_schema.tables WHERE table_schema = 'public';
-- SELECT COUNT(*) AS user_count FROM users;
-- SELECT COUNT(*) AS vehicle_count FROM vehicles;
-- SELECT tablename, indexname FROM pg_indexes WHERE schemaname = 'public' ORDER BY tablename, indexname;
