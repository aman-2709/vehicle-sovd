#!/bin/bash

################################################################################
# SOVD WebApp - Ubuntu Setup Script
################################################################################
# This script installs all required dependencies for running the SOVD Command
# WebApp on Ubuntu/Debian-based systems.
#
# Usage:
#   chmod +x scripts/setup-ubuntu.sh
#   ./scripts/setup-ubuntu.sh
#
# Requirements:
#   - Ubuntu 20.04+ or Debian 11+
#   - sudo privileges
################################################################################

set -e  # Exit on error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if script is run with sudo
check_sudo() {
    if [ "$EUID" -eq 0 ]; then
        log_error "Please do not run this script as root or with sudo"
        log_info "The script will prompt for sudo when needed"
        exit 1
    fi
}

# Check OS compatibility
check_os() {
    log_info "Checking OS compatibility..."

    if [ -f /etc/os-release ]; then
        . /etc/os-release
        if [[ "$ID" != "ubuntu" && "$ID" != "debian" ]]; then
            log_error "This script is designed for Ubuntu/Debian systems only"
            log_info "Detected OS: $NAME"
            exit 1
        fi
        log_success "OS compatibility check passed: $NAME $VERSION"
    else
        log_error "Unable to detect operating system"
        exit 1
    fi
}

# Update system packages
update_system() {
    log_info "Updating system packages..."
    sudo apt-get update -qq
    log_success "System package list updated"
}

# Install basic utilities
install_utilities() {
    log_info "Installing basic utilities (curl, wget, ca-certificates, gnupg)..."
    sudo apt-get install -y -qq \
        curl \
        wget \
        ca-certificates \
        gnupg \
        lsb-release \
        software-properties-common \
        apt-transport-https
    log_success "Basic utilities installed"
}

# Install Make
install_make() {
    if command -v make &> /dev/null; then
        log_success "Make is already installed ($(make --version | head -n1))"
    else
        log_info "Installing Make..."
        sudo apt-get install -y -qq make
        log_success "Make installed"
    fi
}

# Install Git
install_git() {
    if command -v git &> /dev/null; then
        log_success "Git is already installed ($(git --version))"
    else
        log_info "Installing Git..."
        sudo apt-get install -y -qq git
        log_success "Git installed"
    fi
}

# Install Docker
install_docker() {
    if command -v docker &> /dev/null; then
        log_success "Docker is already installed ($(docker --version))"
    else
        log_info "Installing Docker..."

        # Remove old versions if any
        sudo apt-get remove -y -qq docker docker-engine docker.io containerd runc 2>/dev/null || true

        # Add Docker's official GPG key
        sudo install -m 0755 -d /etc/apt/keyrings
        curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
        sudo chmod a+r /etc/apt/keyrings/docker.gpg

        # Set up Docker repository
        echo \
          "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
          $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

        # Install Docker Engine
        sudo apt-get update -qq
        sudo apt-get install -y -qq docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

        log_success "Docker installed ($(docker --version))"
    fi
}

# Configure Docker for non-root user
configure_docker() {
    log_info "Configuring Docker for non-root user..."

    # Add current user to docker group
    if ! groups $USER | grep -q docker; then
        sudo usermod -aG docker $USER
        log_success "User '$USER' added to docker group"
        log_warning "You need to log out and log back in for group membership to take effect"
        log_warning "Alternatively, run: newgrp docker"
    else
        log_success "User '$USER' is already in docker group"
    fi

    # Enable Docker service
    sudo systemctl enable docker --quiet
    sudo systemctl start docker
    log_success "Docker service enabled and started"
}

# Install Docker Compose (standalone, if not already via plugin)
install_docker_compose() {
    if docker compose version &> /dev/null; then
        log_success "Docker Compose plugin is already installed ($(docker compose version))"
    elif command -v docker-compose &> /dev/null; then
        log_success "Docker Compose (standalone) is already installed ($(docker-compose --version))"
    else
        log_info "Installing Docker Compose (standalone)..."
        COMPOSE_VERSION=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | grep 'tag_name' | cut -d\" -f4)
        sudo curl -L "https://github.com/docker/compose/releases/download/${COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" \
            -o /usr/local/bin/docker-compose
        sudo chmod +x /usr/local/bin/docker-compose
        log_success "Docker Compose installed ($(docker-compose --version))"
    fi
}

# Install optional development tools
install_dev_tools() {
    log_info "Installing optional development tools..."

    # Python 3.11+
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
        log_success "Python is already installed (Python $PYTHON_VERSION)"
    else
        log_info "Installing Python 3..."
        sudo apt-get install -y -qq python3 python3-pip python3-venv
        log_success "Python 3 installed"
    fi

    # Node.js 18+
    if command -v node &> /dev/null; then
        NODE_VERSION=$(node --version)
        log_success "Node.js is already installed ($NODE_VERSION)"
    else
        log_info "Installing Node.js 18 LTS..."
        curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
        sudo apt-get install -y -qq nodejs
        log_success "Node.js installed ($(node --version))"
    fi

    # PostgreSQL client tools
    if command -v psql &> /dev/null; then
        log_success "PostgreSQL client is already installed ($(psql --version))"
    else
        log_info "Installing PostgreSQL client tools..."
        sudo apt-get install -y -qq postgresql-client
        log_success "PostgreSQL client installed"
    fi
}

# Verify installation
verify_installation() {
    log_info "Verifying installation..."

    local failed=0

    # Check Docker
    if docker --version &> /dev/null; then
        log_success "✓ Docker: $(docker --version)"
    else
        log_error "✗ Docker not found"
        failed=1
    fi

    # Check Docker Compose
    if docker compose version &> /dev/null; then
        log_success "✓ Docker Compose: $(docker compose version)"
    elif docker-compose --version &> /dev/null; then
        log_success "✓ Docker Compose: $(docker-compose --version)"
    else
        log_error "✗ Docker Compose not found"
        failed=1
    fi

    # Check Make
    if make --version &> /dev/null; then
        log_success "✓ Make: $(make --version | head -n1)"
    else
        log_error "✗ Make not found"
        failed=1
    fi

    # Check Git
    if git --version &> /dev/null; then
        log_success "✓ Git: $(git --version)"
    else
        log_error "✗ Git not found"
        failed=1
    fi

    # Check optional tools
    if python3 --version &> /dev/null; then
        log_success "✓ Python: $(python3 --version)"
    else
        log_warning "○ Python not found (optional)"
    fi

    if node --version &> /dev/null; then
        log_success "✓ Node.js: $(node --version)"
    else
        log_warning "○ Node.js not found (optional)"
    fi

    if psql --version &> /dev/null; then
        log_success "✓ PostgreSQL client: $(psql --version)"
    else
        log_warning "○ PostgreSQL client not found (optional)"
    fi

    if [ $failed -eq 1 ]; then
        log_error "Some required dependencies failed to install"
        exit 1
    fi
}

# Check port availability
check_ports() {
    log_info "Checking port availability..."

    local ports=(3000 8000 5432 6379 9090 3001)
    local occupied_ports=()

    for port in "${ports[@]}"; do
        if sudo lsof -i :$port &> /dev/null; then
            occupied_ports+=($port)
        fi
    done

    if [ ${#occupied_ports[@]} -gt 0 ]; then
        log_warning "The following ports are currently in use: ${occupied_ports[*]}"
        log_warning "You may need to stop services using these ports before running SOVD WebApp"
        log_info "To find process using a port: sudo lsof -i :<port>"
        log_info "To kill process: sudo kill -9 <pid>"
    else
        log_success "All required ports are available (3000, 8000, 5432, 6379, 9090, 3001)"
    fi
}

# Main installation flow
main() {
    echo ""
    echo "╔═══════════════════════════════════════════════════════════╗"
    echo "║       SOVD Command WebApp - Ubuntu Setup Script          ║"
    echo "╚═══════════════════════════════════════════════════════════╝"
    echo ""

    check_sudo
    check_os

    log_info "This script will install:"
    echo "  • Docker Engine"
    echo "  • Docker Compose"
    echo "  • Make"
    echo "  • Git"
    echo "  • Python 3 (optional, for backend development)"
    echo "  • Node.js 18+ (optional, for frontend development)"
    echo "  • PostgreSQL client (optional, for database access)"
    echo ""

    read -p "Do you want to continue? (y/N) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "Installation cancelled"
        exit 0
    fi

    echo ""
    log_info "Starting installation..."

    update_system
    install_utilities
    install_make
    install_git
    install_docker
    configure_docker
    install_docker_compose

    echo ""
    read -p "Do you want to install optional development tools? (y/N) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        install_dev_tools
    else
        log_info "Skipping optional development tools"
    fi

    echo ""
    verify_installation
    check_ports

    echo ""
    log_success "╔═══════════════════════════════════════════════════════════╗"
    log_success "║           Installation completed successfully!           ║"
    log_success "╚═══════════════════════════════════════════════════════════╝"
    echo ""

    log_warning "IMPORTANT: Docker permissions"
    log_warning "If you were added to the docker group, you need to:"
    log_warning "  1. Log out and log back in, OR"
    log_warning "  2. Run: newgrp docker"
    echo ""

    log_info "Next steps:"
    echo "  1. Clone the repository (if not already done):"
    echo "     git clone git@github.com:aman-2709/vehicle-sovd.git"
    echo ""
    echo "  2. Navigate to project directory:"
    echo "     cd vehicle-sovd"
    echo ""
    echo "  3. Start the application:"
    echo "     make up"
    echo ""
    echo "  4. Initialize database (first time only):"
    echo "     POSTGRES_PASSWORD=sovd_pass ./scripts/init_db.sh"
    echo ""
    echo "  5. Access the application:"
    echo "     Frontend: http://localhost:3000"
    echo "     Backend:  http://localhost:8000"
    echo "     API Docs: http://localhost:8000/docs"
    echo ""

    log_info "For more information, see README.md"
    echo ""
}

# Run main function
main "$@"
