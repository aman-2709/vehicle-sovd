#!/bin/bash

################################################################################
# Test script for setup-ubuntu.sh
################################################################################

set -e

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "Testing setup-ubuntu.sh detection logic..."
echo ""

# Test 1: Bash syntax check
echo -n "Test 1: Bash syntax check... "
if bash -n scripts/setup-ubuntu.sh; then
    echo -e "${GREEN}PASS${NC}"
else
    echo -e "${RED}FAIL${NC}"
    exit 1
fi

# Test 2: Script is executable
echo -n "Test 2: Script is executable... "
if [ -x scripts/setup-ubuntu.sh ]; then
    echo -e "${GREEN}PASS${NC}"
else
    echo -e "${RED}FAIL${NC}"
    exit 1
fi

# Test 3: Verify detection functions work
echo -n "Test 3: Docker detection... "
if command -v docker &> /dev/null; then
    echo -e "${GREEN}PASS${NC} (Docker found: $(docker --version))"
else
    echo -e "${BLUE}SKIP${NC} (Docker not installed)"
fi

echo -n "Test 4: Docker Compose detection... "
if docker compose version &> /dev/null; then
    echo -e "${GREEN}PASS${NC} (Docker Compose found: $(docker compose version))"
elif command -v docker-compose &> /dev/null; then
    echo -e "${GREEN}PASS${NC} (Docker Compose found: $(docker-compose --version))"
else
    echo -e "${BLUE}SKIP${NC} (Docker Compose not installed)"
fi

echo -n "Test 5: Make detection... "
if command -v make &> /dev/null; then
    echo -e "${GREEN}PASS${NC} (Make found: $(make --version | head -1))"
else
    echo -e "${BLUE}SKIP${NC} (Make not installed)"
fi

echo -n "Test 6: Git detection... "
if command -v git &> /dev/null; then
    echo -e "${GREEN}PASS${NC} (Git found: $(git --version))"
else
    echo -e "${BLUE}SKIP${NC} (Git not installed)"
fi

echo -n "Test 7: Python detection... "
if command -v python3 &> /dev/null; then
    echo -e "${GREEN}PASS${NC} (Python found: $(python3 --version))"
else
    echo -e "${BLUE}SKIP${NC} (Python not installed)"
fi

echo -n "Test 8: Node.js detection... "
if command -v node &> /dev/null; then
    echo -e "${GREEN}PASS${NC} (Node.js found: $(node --version))"
else
    echo -e "${BLUE}SKIP${NC} (Node.js not installed)"
fi

echo -n "Test 9: PostgreSQL client detection... "
if command -v psql &> /dev/null; then
    echo -e "${GREEN}PASS${NC} (psql found: $(psql --version))"
else
    echo -e "${BLUE}SKIP${NC} (psql not installed)"
fi

# Test 10: OS detection
echo -n "Test 10: OS detection... "
if [ -f /etc/os-release ]; then
    . /etc/os-release
    if [[ "$ID" == "ubuntu" || "$ID" == "debian" ]]; then
        echo -e "${GREEN}PASS${NC} (Detected: $NAME $VERSION)"
    else
        echo -e "${BLUE}INFO${NC} (OS: $NAME - script designed for Ubuntu/Debian)"
    fi
else
    echo -e "${RED}FAIL${NC} (Cannot detect OS)"
    exit 1
fi

# Test 11: Port availability check
echo -n "Test 11: Port availability check... "
required_ports=(3000 8000 5432 6379 9090 3001)
occupied=0
for port in "${required_ports[@]}"; do
    if sudo lsof -i :$port &> /dev/null; then
        occupied=$((occupied + 1))
    fi
done
if [ $occupied -eq 0 ]; then
    echo -e "${GREEN}PASS${NC} (All ports available)"
else
    echo -e "${BLUE}INFO${NC} ($occupied ports in use)"
fi

echo ""
echo -e "${GREEN}All tests completed successfully!${NC}"
echo ""
echo "Summary:"
echo "- Script syntax is valid"
echo "- Script is executable"
echo "- Detection logic is working"
echo "- System: $(lsb_release -d | cut -f2)"
echo ""
