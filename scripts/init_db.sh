#!/bin/bash
# ============================================================================
# SOVD Database Initialization Script
# Description: Initializes PostgreSQL database with schema and seed data
# Usage: ./scripts/init_db.sh
# Environment Variables:
#   POSTGRES_HOST     - Database host (default: localhost)
#   POSTGRES_PORT     - Database port (default: 5432)
#   POSTGRES_DB       - Database name (default: sovd)
#   POSTGRES_USER     - Database user (default: postgres)
#   POSTGRES_PASSWORD - Database password (required)
#   DATABASE_URL      - Full connection URL (overrides individual params)
# ============================================================================

set -e  # Exit immediately on error
set -u  # Exit on undefined variable
set -o pipefail  # Exit on pipe failure

# ============================================================================
# Configuration
# ============================================================================

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Database connection parameters with defaults
POSTGRES_HOST="${POSTGRES_HOST:-localhost}"
POSTGRES_PORT="${POSTGRES_PORT:-5432}"
POSTGRES_DB="${POSTGRES_DB:-sovd}"
POSTGRES_USER="${POSTGRES_USER:-postgres}"
POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-}"

# Maximum retries for connection
MAX_RETRIES=30
RETRY_INTERVAL=2

# Script directory and SQL file location
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
SQL_FILE="$PROJECT_ROOT/docs/api/initial_schema.sql"

# ============================================================================
# Functions
# ============================================================================

# Print colored message
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

# Build psql command with connection parameters
get_psql_cmd() {
    if [ -n "${DATABASE_URL:-}" ]; then
        echo "psql \"$DATABASE_URL\""
    else
        echo "PGPASSWORD='$POSTGRES_PASSWORD' psql -h $POSTGRES_HOST -p $POSTGRES_PORT -U $POSTGRES_USER -d $POSTGRES_DB"
    fi
}

# Check if PostgreSQL is ready
wait_for_postgres() {
    print_info "Waiting for PostgreSQL to be ready..."

    local retry_count=0

    while [ $retry_count -lt $MAX_RETRIES ]; do
        if [ -n "${DATABASE_URL:-}" ]; then
            # Check using DATABASE_URL
            if psql "$DATABASE_URL" -c "SELECT 1" > /dev/null 2>&1; then
                print_success "PostgreSQL is ready!"
                return 0
            fi
        else
            # Check using pg_isready if available, otherwise try connection
            if command -v pg_isready > /dev/null 2>&1; then
                if PGPASSWORD="$POSTGRES_PASSWORD" pg_isready -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" > /dev/null 2>&1; then
                    print_success "PostgreSQL is ready!"
                    return 0
                fi
            else
                # Fallback: try to connect
                if PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d postgres -c "SELECT 1" > /dev/null 2>&1; then
                    print_success "PostgreSQL is ready!"
                    return 0
                fi
            fi
        fi

        retry_count=$((retry_count + 1))
        print_info "Attempt $retry_count/$MAX_RETRIES - PostgreSQL not ready yet, waiting ${RETRY_INTERVAL}s..."
        sleep $RETRY_INTERVAL
    done

    print_error "PostgreSQL did not become ready after $MAX_RETRIES attempts"
    return 1
}

# Execute SQL file
execute_sql_file() {
    print_info "Executing SQL schema file: $SQL_FILE"

    if [ ! -f "$SQL_FILE" ]; then
        print_error "SQL file not found: $SQL_FILE"
        return 1
    fi

    if [ -n "${DATABASE_URL:-}" ]; then
        if psql "$DATABASE_URL" -f "$SQL_FILE" -v ON_ERROR_STOP=1; then
            print_success "SQL schema executed successfully"
            return 0
        else
            print_error "Failed to execute SQL schema"
            return 1
        fi
    else
        if PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -f "$SQL_FILE" -v ON_ERROR_STOP=1; then
            print_success "SQL schema executed successfully"
            return 0
        else
            print_error "Failed to execute SQL schema"
            return 1
        fi
    fi
}

# Verify tables were created
verify_tables() {
    print_info "Verifying table creation..."

    local psql_cmd=$(get_psql_cmd)
    local expected_tables=("users" "vehicles" "commands" "responses" "sessions" "audit_logs")
    local table_count

    if [ -n "${DATABASE_URL:-}" ]; then
        table_count=$(psql "$DATABASE_URL" -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE';" | xargs)
    else
        table_count=$(PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE';" | xargs)
    fi

    if [ "$table_count" -eq 6 ]; then
        print_success "All 6 tables created successfully"

        # Verify each table exists
        for table in "${expected_tables[@]}"; do
            local exists
            if [ -n "${DATABASE_URL:-}" ]; then
                exists=$(psql "$DATABASE_URL" -t -c "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = '$table');" | xargs)
            else
                exists=$(PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -t -c "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = '$table');" | xargs)
            fi

            if [ "$exists" = "t" ]; then
                print_success "  ✓ Table '$table' exists"
            else
                print_error "  ✗ Table '$table' does not exist"
                return 1
            fi
        done
    else
        print_error "Expected 6 tables, found $table_count"
        return 1
    fi
}

# Verify indexes were created
verify_indexes() {
    print_info "Verifying index creation..."

    local index_count

    if [ -n "${DATABASE_URL:-}" ]; then
        index_count=$(psql "$DATABASE_URL" -t -c "SELECT COUNT(*) FROM pg_indexes WHERE schemaname = 'public';" | xargs)
    else
        index_count=$(PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -t -c "SELECT COUNT(*) FROM pg_indexes WHERE schemaname = 'public';" | xargs)
    fi

    # We expect at least 21 indexes (excluding automatic primary key indexes)
    if [ "$index_count" -ge 21 ]; then
        print_success "Created $index_count indexes (minimum 21 required)"
    else
        print_warning "Created $index_count indexes (expected at least 21)"
        # Don't fail, just warn - some indexes might be implicit
    fi
}

# Verify seed data was inserted
verify_seed_data() {
    print_info "Verifying seed data insertion..."

    local user_count
    local vehicle_count

    # Check users
    if [ -n "${DATABASE_URL:-}" ]; then
        user_count=$(psql "$DATABASE_URL" -t -c "SELECT COUNT(*) FROM users;" | xargs)
    else
        user_count=$(PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -t -c "SELECT COUNT(*) FROM users;" | xargs)
    fi

    if [ "$user_count" -eq 2 ]; then
        print_success "  ✓ 2 users inserted (admin, engineer)"
    else
        print_error "  ✗ Expected 2 users, found $user_count"
        return 1
    fi

    # Check vehicles
    if [ -n "${DATABASE_URL:-}" ]; then
        vehicle_count=$(psql "$DATABASE_URL" -t -c "SELECT COUNT(*) FROM vehicles;" | xargs)
    else
        vehicle_count=$(PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -t -c "SELECT COUNT(*) FROM vehicles;" | xargs)
    fi

    if [ "$vehicle_count" -eq 2 ]; then
        print_success "  ✓ 2 vehicles inserted (TESTVIN0000000001, TESTVIN0000000002)"
    else
        print_error "  ✗ Expected 2 vehicles, found $vehicle_count"
        return 1
    fi

    # Verify specific seed data
    local admin_exists
    local engineer_exists
    local tesla_exists
    local bmw_exists

    if [ -n "${DATABASE_URL:-}" ]; then
        admin_exists=$(psql "$DATABASE_URL" -t -c "SELECT EXISTS (SELECT 1 FROM users WHERE username = 'admin' AND role = 'admin');" | xargs)
        engineer_exists=$(psql "$DATABASE_URL" -t -c "SELECT EXISTS (SELECT 1 FROM users WHERE username = 'engineer' AND role = 'engineer');" | xargs)
        tesla_exists=$(psql "$DATABASE_URL" -t -c "SELECT EXISTS (SELECT 1 FROM vehicles WHERE vin = 'TESTVIN0000000001');" | xargs)
        bmw_exists=$(psql "$DATABASE_URL" -t -c "SELECT EXISTS (SELECT 1 FROM vehicles WHERE vin = 'TESTVIN0000000002');" | xargs)
    else
        admin_exists=$(PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -t -c "SELECT EXISTS (SELECT 1 FROM users WHERE username = 'admin' AND role = 'admin');" | xargs)
        engineer_exists=$(PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -t -c "SELECT EXISTS (SELECT 1 FROM users WHERE username = 'engineer' AND role = 'engineer');" | xargs)
        tesla_exists=$(PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -t -c "SELECT EXISTS (SELECT 1 FROM vehicles WHERE vin = 'TESTVIN0000000001');" | xargs)
        bmw_exists=$(PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -t -c "SELECT EXISTS (SELECT 1 FROM vehicles WHERE vin = 'TESTVIN0000000002');" | xargs)
    fi

    [ "$admin_exists" = "t" ] && print_success "  ✓ Admin user exists" || { print_error "  ✗ Admin user missing"; return 1; }
    [ "$engineer_exists" = "t" ] && print_success "  ✓ Engineer user exists" || { print_error "  ✗ Engineer user missing"; return 1; }
    [ "$tesla_exists" = "t" ] && print_success "  ✓ Tesla test vehicle exists" || { print_error "  ✗ Tesla test vehicle missing"; return 1; }
    [ "$bmw_exists" = "t" ] && print_success "  ✓ BMW test vehicle exists" || { print_error "  ✗ BMW test vehicle missing"; return 1; }
}

# Print database summary
print_summary() {
    print_info "Database initialization summary:"

    if [ -n "${DATABASE_URL:-}" ]; then
        echo "  Database URL: ${DATABASE_URL}"
    else
        echo "  Host: ${POSTGRES_HOST}"
        echo "  Port: ${POSTGRES_PORT}"
        echo "  Database: ${POSTGRES_DB}"
        echo "  User: ${POSTGRES_USER}"
    fi

    echo ""
    print_success "Seed Data Credentials:"
    echo "  Admin User:"
    echo "    Username: admin"
    echo "    Password: admin123"
    echo "    Role: admin"
    echo ""
    echo "  Engineer User:"
    echo "    Username: engineer"
    echo "    Password: engineer123"
    echo "    Role: engineer"
    echo ""
    echo "  Test Vehicles:"
    echo "    VIN: TESTVIN0000000001 (Tesla Model 3 2023, connected)"
    echo "    VIN: TESTVIN0000000002 (BMW X5 2022, disconnected)"
}

# ============================================================================
# Main Execution
# ============================================================================

main() {
    echo ""
    print_info "=========================================="
    print_info "SOVD Database Initialization"
    print_info "=========================================="
    echo ""

    # Check if password is provided
    if [ -z "${DATABASE_URL:-}" ] && [ -z "${POSTGRES_PASSWORD:-}" ]; then
        print_error "POSTGRES_PASSWORD environment variable is required (or provide DATABASE_URL)"
        print_info "Usage: POSTGRES_PASSWORD=yourpassword ./scripts/init_db.sh"
        exit 1
    fi

    # Check if psql is available
    if ! command -v psql > /dev/null 2>&1; then
        print_error "psql command not found. Please install PostgreSQL client tools."
        exit 1
    fi

    # Wait for PostgreSQL to be ready
    if ! wait_for_postgres; then
        print_error "Failed to connect to PostgreSQL"
        exit 1
    fi

    echo ""

    # Execute SQL file
    if ! execute_sql_file; then
        print_error "Database initialization failed during schema creation"
        exit 1
    fi

    echo ""

    # Verify tables
    if ! verify_tables; then
        print_error "Database initialization failed during table verification"
        exit 1
    fi

    echo ""

    # Verify indexes
    verify_indexes

    echo ""

    # Verify seed data
    if ! verify_seed_data; then
        print_error "Database initialization failed during seed data verification"
        exit 1
    fi

    echo ""
    print_summary

    echo ""
    print_success "=========================================="
    print_success "Database initialization completed successfully!"
    print_success "=========================================="
    echo ""

    exit 0
}

# Run main function
main "$@"
