#!/bin/bash

# Vogelring Migration Runner Script
# This script provides a convenient way to run the migration process

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Function to print colored output
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
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [COMMAND] [OPTIONS]"
    echo ""
    echo "Commands:"
    echo "  setup       - Test migration setup and dependencies"
    echo "  dry-run     - Run migration in dry-run mode (no changes)"
    echo "  migrate     - Run complete migration"
    echo "  validate    - Validate existing data integrity"
    echo "  truncate    - Truncate tables and run migration (DESTRUCTIVE)"
    echo ""
    echo "Options:"
    echo "  --user USER - Specify user for S3 sighting files (default: from env)"
    echo "  --help      - Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 setup                    # Test setup"
    echo "  $0 dry-run                  # Test migration"
    echo "  $0 migrate                  # Run migration"
    echo "  $0 migrate --user john.doe  # Run migration for specific user"
    echo "  $0 validate                 # Validate data"
}

# Function to check prerequisites
check_prerequisites() {
    print_info "Checking prerequisites..."
    
    # Check Python
    if ! command_exists python3; then
        print_error "Python 3 is required but not installed"
        exit 1
    fi
    
    # Check if we're in the right directory
    if [[ ! -f "$SCRIPT_DIR/migrate_all.py" ]]; then
        print_error "Migration scripts not found. Please run from the migration directory."
        exit 1
    fi
    
    # Check if .env file exists
    if [[ ! -f "$SCRIPT_DIR/.env" ]]; then
        print_warning ".env file not found. Please copy .env.example to .env and configure it."
        if [[ -f "$SCRIPT_DIR/.env.example" ]]; then
            print_info "You can copy the example file:"
            print_info "  cp .env.example .env"
        fi
        exit 1
    fi
    
    # Check if requirements are installed
    if ! python3 -c "import boto3, psycopg2, sqlalchemy, pydantic" >/dev/null 2>&1; then
        print_warning "Some Python dependencies may be missing."
        print_info "Install them with: pip install -r requirements.txt"
    fi
    
    print_success "Prerequisites check passed"
}

# Function to run setup test
run_setup() {
    print_info "Running migration setup test..."
    cd "$SCRIPT_DIR"
    python3 test_setup.py
}

# Function to run dry-run migration
run_dry_run() {
    local user_arg=""
    if [[ -n "$USER_ARG" ]]; then
        user_arg="--user $USER_ARG"
    fi
    
    print_info "Running migration in dry-run mode..."
    cd "$SCRIPT_DIR"
    python3 migrate_all.py --dry-run $user_arg
}

# Function to run actual migration
run_migration() {
    local user_arg=""
    if [[ -n "$USER_ARG" ]]; then
        user_arg="--user $USER_ARG"
    fi
    
    print_warning "This will migrate data from AWS to PostgreSQL."
    print_warning "Make sure you have:"
    print_warning "  1. Configured AWS credentials"
    print_warning "  2. Set up PostgreSQL database"
    print_warning "  3. Configured .env file"
    print_warning "  4. Run 'setup' and 'dry-run' commands first"
    echo ""
    read -p "Continue with migration? (y/N): " -n 1 -r
    echo
    
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_info "Migration cancelled"
        exit 0
    fi
    
    print_info "Running complete migration..."
    cd "$SCRIPT_DIR"
    python3 migrate_all.py $user_arg
}

# Function to run validation
run_validation() {
    print_info "Running data validation..."
    cd "$SCRIPT_DIR"
    python3 migrate_dynamodb.py --validate-only
    
    local user_arg=""
    if [[ -n "$USER_ARG" ]]; then
        user_arg="--user $USER_ARG"
    fi
    python3 migrate_s3_pickle.py --validate-only $user_arg
}

# Function to run truncate and migrate
run_truncate_migrate() {
    local user_arg=""
    if [[ -n "$USER_ARG" ]]; then
        user_arg="--user $USER_ARG"
    fi
    
    print_error "WARNING: This will DELETE ALL existing data in PostgreSQL tables!"
    print_error "This action cannot be undone."
    echo ""
    read -p "Are you absolutely sure? Type 'DELETE ALL DATA' to continue: " -r
    echo
    
    if [[ "$REPLY" != "DELETE ALL DATA" ]]; then
        print_info "Truncate operation cancelled"
        exit 0
    fi
    
    print_info "Truncating tables and running migration..."
    cd "$SCRIPT_DIR"
    python3 migrate_all.py --truncate $user_arg
}

# Parse command line arguments
COMMAND=""
USER_ARG=""

while [[ $# -gt 0 ]]; do
    case $1 in
        setup|dry-run|migrate|validate|truncate)
            COMMAND="$1"
            shift
            ;;
        --user)
            USER_ARG="$2"
            shift 2
            ;;
        --help|-h)
            show_usage
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Show usage if no command provided
if [[ -z "$COMMAND" ]]; then
    show_usage
    exit 1
fi

# Check prerequisites for all commands except help
check_prerequisites

# Run the appropriate command
case $COMMAND in
    setup)
        run_setup
        ;;
    dry-run)
        run_dry_run
        ;;
    migrate)
        run_migration
        ;;
    validate)
        run_validation
        ;;
    truncate)
        run_truncate_migrate
        ;;
    *)
        print_error "Unknown command: $COMMAND"
        show_usage
        exit 1
        ;;
esac