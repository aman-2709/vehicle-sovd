#!/bin/bash

# Database Migration Testing Script
# Tests Alembic migrations by applying, verifying, and rolling back
#
# Usage:
#   ./scripts/test_migration.sh [DATABASE_URL]
#
# Environment Variables:
#   DATABASE_URL: PostgreSQL connection string (optional, defaults to local dev database)
#                 Format: postgresql+asyncpg://user:password@host:port/database
#
# Exit Codes:
#   0: All tests passed
#   1: Migration upgrade failed
#   2: Schema verification failed
#   3: Migration downgrade failed
#   4: Rollback verification failed

set -e  # Exit on error
set -u  # Exit on undefined variable

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default database URL for local testing
DEFAULT_DATABASE_URL="postgresql+asyncpg://sovd_user:sovd_pass@localhost:5432/sovd"

# Use provided DATABASE_URL or default
export DATABASE_URL="${1:-${DATABASE_URL:-$DEFAULT_DATABASE_URL}}"

# Extract database connection info for psql (convert asyncpg to psycopg2 format for psql)
DB_HOST=$(echo "$DATABASE_URL" | sed -n 's|.*@\([^:]*\):.*|\1|p')
DB_PORT=$(echo "$DATABASE_URL" | sed -n 's|.*:\([0-9]*\)/.*|\1|p')
DB_NAME=$(echo "$DATABASE_URL" | sed -n 's|.*/\([^?]*\).*|\1|p')
DB_USER=$(echo "$DATABASE_URL" | sed -n 's|.*://\([^:]*\):.*|\1|p')
DB_PASS=$(echo "$DATABASE_URL" | sed -n 's|.*://[^:]*:\([^@]*\)@.*|\1|p')

# Change to backend directory where alembic.ini is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BACKEND_DIR="$PROJECT_ROOT/backend"

if [ ! -d "$BACKEND_DIR" ]; then
    echo -e "${RED}✗ Backend directory not found: $BACKEND_DIR${NC}"
    exit 1
fi

cd "$BACKEND_DIR"

echo -e "${BLUE}==================================================================${NC}"
echo -e "${BLUE}Database Migration Testing${NC}"
echo -e "${BLUE}==================================================================${NC}"
echo ""
echo -e "${YELLOW}Configuration:${NC}"
echo -e "  Database Host: $DB_HOST"
echo -e "  Database Port: $DB_PORT"
echo -e "  Database Name: $DB_NAME"
echo -e "  Database User: $DB_USER"
echo -e "  Working Directory: $BACKEND_DIR"
echo ""

# Function to check database connectivity
check_database_connection() {
    echo -e "${YELLOW}Checking database connectivity...${NC}"

    export PGPASSWORD="$DB_PASS"

    if psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "SELECT 1;" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Database connection successful${NC}"
        return 0
    else
        echo -e "${RED}✗ Cannot connect to database${NC}"
        echo -e "${RED}  Please ensure the database is running and credentials are correct${NC}"
        return 1
    fi
}

# Function to get current migration revision
get_current_revision() {
    alembic current --verbose 2>/dev/null | grep -oP '(?<=Rev: )[a-f0-9]+' || echo "base"
}

# Function to count tables in database
count_tables() {
    export PGPASSWORD="$DB_PASS"
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c \
        "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';" 2>/dev/null | xargs
}

# Function to verify expected tables exist
verify_schema() {
    export PGPASSWORD="$DB_PASS"

    echo -e "${YELLOW}Verifying database schema...${NC}"

    # Expected tables from initial migration
    EXPECTED_TABLES=("users" "vehicles" "commands" "command_responses" "alembic_version")

    for table in "${EXPECTED_TABLES[@]}"; do
        TABLE_EXISTS=$(psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c \
            "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public' AND table_name = '$table';" 2>/dev/null | xargs)

        if [ "$TABLE_EXISTS" = "1" ]; then
            echo -e "${GREEN}  ✓ Table '$table' exists${NC}"
        else
            echo -e "${RED}  ✗ Table '$table' NOT found${NC}"
            return 1
        fi
    done

    return 0
}

# Function to insert test data
insert_test_data() {
    export PGPASSWORD="$DB_PASS"

    echo -e "${YELLOW}Inserting test data...${NC}"

    # Insert a test user
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c \
        "INSERT INTO users (email, hashed_password, full_name, role, is_active)
         VALUES ('test@example.com', 'hashed_password', 'Test User', 'engineer', true)
         ON CONFLICT (email) DO NOTHING;" > /dev/null 2>&1

    echo -e "${GREEN}  ✓ Test data inserted${NC}"
}

# Function to verify test data exists
verify_test_data() {
    export PGPASSWORD="$DB_PASS"

    USER_COUNT=$(psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c \
        "SELECT COUNT(*) FROM users WHERE email = 'test@example.com';" 2>/dev/null | xargs)

    if [ "$USER_COUNT" = "1" ]; then
        echo -e "${GREEN}  ✓ Test data verified${NC}"
        return 0
    else
        echo -e "${RED}  ✗ Test data NOT found${NC}"
        return 1
    fi
}

# Main test flow
main() {
    echo -e "${BLUE}------------------------------------------------------------------${NC}"
    echo -e "${BLUE}Step 1: Database Connectivity Test${NC}"
    echo -e "${BLUE}------------------------------------------------------------------${NC}"

    if ! check_database_connection; then
        exit 1
    fi
    echo ""

    echo -e "${BLUE}------------------------------------------------------------------${NC}"
    echo -e "${BLUE}Step 2: Get Current Migration State${NC}"
    echo -e "${BLUE}------------------------------------------------------------------${NC}"

    INITIAL_REVISION=$(get_current_revision)
    INITIAL_TABLE_COUNT=$(count_tables)

    echo -e "${YELLOW}Current state:${NC}"
    echo -e "  Revision: $INITIAL_REVISION"
    echo -e "  Tables: $INITIAL_TABLE_COUNT"
    echo ""

    echo -e "${BLUE}------------------------------------------------------------------${NC}"
    echo -e "${BLUE}Step 3: Apply Migration (alembic upgrade head)${NC}"
    echo -e "${BLUE}------------------------------------------------------------------${NC}"

    if alembic upgrade head; then
        echo -e "${GREEN}✓ Migration upgrade successful${NC}"
    else
        echo -e "${RED}✗ Migration upgrade failed${NC}"
        exit 1
    fi
    echo ""

    echo -e "${BLUE}------------------------------------------------------------------${NC}"
    echo -e "${BLUE}Step 4: Verify Schema After Upgrade${NC}"
    echo -e "${BLUE}------------------------------------------------------------------${NC}"

    AFTER_UPGRADE_REVISION=$(get_current_revision)
    AFTER_UPGRADE_TABLE_COUNT=$(count_tables)

    echo -e "${YELLOW}After upgrade:${NC}"
    echo -e "  Revision: $AFTER_UPGRADE_REVISION"
    echo -e "  Tables: $AFTER_UPGRADE_TABLE_COUNT"
    echo ""

    if verify_schema; then
        echo -e "${GREEN}✓ Schema verification successful${NC}"
    else
        echo -e "${RED}✗ Schema verification failed${NC}"
        exit 2
    fi
    echo ""

    echo -e "${BLUE}------------------------------------------------------------------${NC}"
    echo -e "${BLUE}Step 5: Insert and Verify Test Data${NC}"
    echo -e "${BLUE}------------------------------------------------------------------${NC}"

    insert_test_data

    if verify_test_data; then
        echo -e "${GREEN}✓ Data insertion successful${NC}"
    else
        echo -e "${RED}✗ Data verification failed${NC}"
        exit 2
    fi
    echo ""

    echo -e "${BLUE}------------------------------------------------------------------${NC}"
    echo -e "${BLUE}Step 6: Test Migration Rollback (alembic downgrade -1)${NC}"
    echo -e "${BLUE}------------------------------------------------------------------${NC}"

    if alembic downgrade -1; then
        echo -e "${GREEN}✓ Migration downgrade successful${NC}"
    else
        echo -e "${RED}✗ Migration downgrade failed${NC}"
        exit 3
    fi
    echo ""

    echo -e "${BLUE}------------------------------------------------------------------${NC}"
    echo -e "${BLUE}Step 7: Verify Schema After Downgrade${NC}"
    echo -e "${BLUE}------------------------------------------------------------------${NC}"

    AFTER_DOWNGRADE_REVISION=$(get_current_revision)
    AFTER_DOWNGRADE_TABLE_COUNT=$(count_tables)

    echo -e "${YELLOW}After downgrade:${NC}"
    echo -e "  Revision: $AFTER_DOWNGRADE_REVISION"
    echo -e "  Tables: $AFTER_DOWNGRADE_TABLE_COUNT"
    echo ""

    # For initial migration, all tables should be removed after downgrade to base
    if [ "$AFTER_DOWNGRADE_REVISION" = "base" ] && [ "$AFTER_DOWNGRADE_TABLE_COUNT" = "0" ]; then
        echo -e "${GREEN}✓ Rollback verification successful (all tables removed)${NC}"
    elif [ "$AFTER_DOWNGRADE_TABLE_COUNT" -lt "$AFTER_UPGRADE_TABLE_COUNT" ]; then
        echo -e "${GREEN}✓ Rollback verification successful (table count decreased)${NC}"
    else
        echo -e "${RED}✗ Rollback verification failed (unexpected table count)${NC}"
        exit 4
    fi
    echo ""

    echo -e "${BLUE}------------------------------------------------------------------${NC}"
    echo -e "${BLUE}Step 8: Re-apply Migration for Clean State${NC}"
    echo -e "${BLUE}------------------------------------------------------------------${NC}"

    if alembic upgrade head; then
        echo -e "${GREEN}✓ Migration re-applied successfully${NC}"
    else
        echo -e "${RED}✗ Migration re-application failed${NC}"
        exit 1
    fi
    echo ""

    echo -e "${GREEN}==================================================================${NC}"
    echo -e "${GREEN}✓ ALL MIGRATION TESTS PASSED${NC}"
    echo -e "${GREEN}==================================================================${NC}"
    echo ""
    echo -e "${YELLOW}Summary:${NC}"
    echo -e "  ✓ Database connection verified"
    echo -e "  ✓ Migration upgrade successful"
    echo -e "  ✓ Schema verification passed"
    echo -e "  ✓ Test data insertion successful"
    echo -e "  ✓ Migration downgrade successful"
    echo -e "  ✓ Rollback verification passed"
    echo -e "  ✓ Migration re-applied successfully"
    echo ""

    return 0
}

# Run main test flow
main

# Cleanup
unset PGPASSWORD
