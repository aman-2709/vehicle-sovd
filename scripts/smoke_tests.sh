#!/bin/bash
# Smoke Tests Script for SOVD Command WebApp
# Tests critical endpoints after deployment to verify basic functionality

set -e

# Configuration
API_BASE_URL=${API_BASE_URL:-http://localhost:8000}
FRONTEND_BASE_URL=${FRONTEND_BASE_URL:-http://localhost:3000}
TIMEOUT=${TIMEOUT:-10}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counter
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0

# Helper function to print test results
print_test() {
    local test_name=$1
    local result=$2
    local message=$3

    TESTS_RUN=$((TESTS_RUN + 1))

    if [ "$result" = "PASS" ]; then
        echo -e "${GREEN}✓ PASS${NC}: $test_name"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "${RED}✗ FAIL${NC}: $test_name - $message"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
}

# Helper function to test HTTP endpoint
test_endpoint() {
    local name=$1
    local url=$2
    local expected_code=${3:-200}

    echo -e "${YELLOW}Testing${NC}: $name ($url)"

    response=$(curl -s -o /dev/null -w "%{http_code}" --max-time $TIMEOUT "$url" 2>&1)

    if [ "$response" = "$expected_code" ]; then
        print_test "$name" "PASS" ""
        return 0
    else
        print_test "$name" "FAIL" "Expected HTTP $expected_code, got $response"
        return 1
    fi
}

# Helper function to test JSON response
test_json_endpoint() {
    local name=$1
    local url=$2
    local expected_field=$3

    echo -e "${YELLOW}Testing${NC}: $name ($url)"

    response=$(curl -s --max-time $TIMEOUT "$url" 2>&1)
    http_code=$(curl -s -o /dev/null -w "%{http_code}" --max-time $TIMEOUT "$url" 2>&1)

    if [ "$http_code" != "200" ]; then
        print_test "$name" "FAIL" "HTTP $http_code"
        return 1
    fi

    # Check if expected field exists in JSON response
    if echo "$response" | grep -q "$expected_field"; then
        print_test "$name" "PASS" ""
        return 0
    else
        print_test "$name" "FAIL" "Expected field '$expected_field' not found in response"
        return 1
    fi
}

echo "========================================"
echo "  SOVD Smoke Tests"
echo "========================================"
echo "API Base URL: $API_BASE_URL"
echo "Frontend Base URL: $FRONTEND_BASE_URL"
echo "Timeout: ${TIMEOUT}s"
echo "========================================"
echo ""

# Test 1: Health endpoint (liveness)
test_endpoint "Backend Health (Liveness)" "$API_BASE_URL/health/live" 200

# Test 2: Readiness endpoint (with DB/Redis)
test_json_endpoint "Backend Health (Readiness)" "$API_BASE_URL/health/ready" "status"

# Test 3: API documentation
test_endpoint "API Documentation (Swagger)" "$API_BASE_URL/docs" 200

# Test 4: OpenAPI spec
test_endpoint "OpenAPI Specification" "$API_BASE_URL/openapi.json" 200

# Test 5: Metrics endpoint
test_endpoint "Prometheus Metrics" "$API_BASE_URL/metrics" 200

# Test 6: Frontend loads
test_endpoint "Frontend Application" "$FRONTEND_BASE_URL/" 200

# Test 7: Frontend static assets (check if Vite/React build is valid)
# Note: This may fail in dev mode, but should pass in production
echo -e "${YELLOW}Testing${NC}: Frontend Static Assets"
frontend_response=$(curl -s --max-time $TIMEOUT "$FRONTEND_BASE_URL/" 2>&1)
if echo "$frontend_response" | grep -q -E "(root|__vite__|react)"; then
    print_test "Frontend Static Assets" "PASS" ""
else
    print_test "Frontend Static Assets" "FAIL" "No Vite/React markers found"
fi

# Test 8: CORS headers (OPTIONS preflight)
echo -e "${YELLOW}Testing${NC}: CORS Headers"
cors_response=$(curl -s -X OPTIONS -H "Origin: http://localhost:3000" \
    -H "Access-Control-Request-Method: POST" \
    -H "Access-Control-Request-Headers: Content-Type" \
    -o /dev/null -w "%{http_code}" --max-time $TIMEOUT \
    "$API_BASE_URL/api/v1/auth/login" 2>&1)

if [ "$cors_response" = "200" ] || [ "$cors_response" = "204" ]; then
    print_test "CORS Headers" "PASS" ""
else
    print_test "CORS Headers" "FAIL" "Expected HTTP 200/204, got $cors_response"
fi

# Summary
echo ""
echo "========================================"
echo "  Smoke Tests Summary"
echo "========================================"
echo -e "Total Tests:  $TESTS_RUN"
echo -e "${GREEN}Passed:       $TESTS_PASSED${NC}"
echo -e "${RED}Failed:       $TESTS_FAILED${NC}"
echo "========================================"

# Exit with failure if any tests failed
if [ $TESTS_FAILED -gt 0 ]; then
    echo -e "${RED}❌ Smoke tests FAILED${NC}"
    exit 1
else
    echo -e "${GREEN}✅ All smoke tests PASSED${NC}"
    exit 0
fi
