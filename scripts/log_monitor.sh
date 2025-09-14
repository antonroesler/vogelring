#!/bin/bash
"""
Log monitoring script for Vogelring application
Provides easy access to application logs and log analysis
"""

set -e

# Configuration
COMPOSE_FILE="docker-compose.yml"
LOG_DIR="./logs"
SERVICES=("postgres" "api" "nginx")

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_debug() {
    echo -e "${BLUE}[DEBUG]${NC} $1"
}

# Function to show usage
show_usage() {
    cat << EOF
Usage: $0 [COMMAND] [OPTIONS]

Commands:
    tail [SERVICE]      Tail logs for a specific service (default: all)
    follow [SERVICE]    Follow logs for a specific service (default: all)
    errors [SERVICE]    Show recent errors for a service (default: all)
    stats               Show log statistics
    clean               Clean old log files
    export [SERVICE]    Export logs to file

Services: ${SERVICES[*]}

Options:
    -h, --help         Show this help message
    -n, --lines N      Number of lines to show (default: 100)
    -s, --since TIME   Show logs since timestamp (e.g., '1h', '30m', '2024-01-01')

Examples:
    $0 tail api                    # Tail API logs
    $0 follow postgres             # Follow PostgreSQL logs
    $0 errors --lines 50           # Show last 50 error lines from all services
    $0 stats                       # Show log statistics
    $0 export api                  # Export API logs to file
EOF
}

# Function to check if Docker Compose is available
check_docker_compose() {
    if ! command -v docker-compose &> /dev/null; then
        log_error "docker-compose not found. Please install Docker Compose."
        exit 1
    fi
    
    if [ ! -f "$COMPOSE_FILE" ]; then
        log_error "Docker Compose file not found: $COMPOSE_FILE"
        exit 1
    fi
}

# Function to get container name for service
get_container_name() {
    local service=$1
    docker-compose ps -q "$service" 2>/dev/null | head -1
}

# Function to tail logs for a service
tail_logs() {
    local service=${1:-}
    local lines=${2:-100}
    local since=${3:-}
    
    local docker_args="--tail $lines"
    if [ -n "$since" ]; then
        docker_args="$docker_args --since $since"
    fi
    
    if [ -n "$service" ]; then
        log_info "Tailing logs for service: $service"
        docker-compose logs $docker_args "$service"
    else
        log_info "Tailing logs for all services"
        docker-compose logs $docker_args
    fi
}

# Function to follow logs for a service
follow_logs() {
    local service=${1:-}
    local lines=${2:-100}
    local since=${3:-}
    
    local docker_args="--tail $lines --follow"
    if [ -n "$since" ]; then
        docker_args="$docker_args --since $since"
    fi
    
    if [ -n "$service" ]; then
        log_info "Following logs for service: $service (Press Ctrl+C to stop)"
        docker-compose logs $docker_args "$service"
    else
        log_info "Following logs for all services (Press Ctrl+C to stop)"
        docker-compose logs $docker_args
    fi
}

# Function to show errors
show_errors() {
    local service=${1:-}
    local lines=${2:-100}
    local since=${3:-}
    
    local docker_args="--tail $lines"
    if [ -n "$since" ]; then
        docker_args="$docker_args --since $since"
    fi
    
    log_info "Searching for errors in logs..."
    
    if [ -n "$service" ]; then
        docker-compose logs $docker_args "$service" 2>&1 | \
            grep -i -E "(error|exception|failed|fatal|critical)" --color=always || \
            log_info "No errors found in $service logs"
    else
        docker-compose logs $docker_args 2>&1 | \
            grep -i -E "(error|exception|failed|fatal|critical)" --color=always || \
            log_info "No errors found in logs"
    fi
}

# Function to show log statistics
show_stats() {
    log_info "Gathering log statistics..."
    
    echo
    echo "=== Container Status ==="
    docker-compose ps
    
    echo
    echo "=== Log Statistics ==="
    for service in "${SERVICES[@]}"; do
        local container=$(get_container_name "$service")
        if [ -n "$container" ]; then
            local log_lines=$(docker logs "$container" 2>&1 | wc -l)
            local error_lines=$(docker logs "$container" 2>&1 | grep -i -E "(error|exception|failed|fatal|critical)" | wc -l)
            echo "Service: $service"
            echo "  Total log lines: $log_lines"
            echo "  Error lines: $error_lines"
            echo
        else
            log_warn "Container not found for service: $service"
        fi
    done
    
    # System resource usage
    echo "=== System Resources ==="
    if command -v free &> /dev/null; then
        echo "Memory usage:"
        free -h
        echo
    fi
    
    if command -v df &> /dev/null; then
        echo "Disk usage:"
        df -h / 2>/dev/null || true
        echo
    fi
    
    # Docker system info
    echo "=== Docker System Info ==="
    docker system df 2>/dev/null || true
}

# Function to clean old logs
clean_logs() {
    log_info "Cleaning old log files..."
    
    # Clean Docker logs (requires root or docker group membership)
    log_info "Truncating Docker container logs..."
    for service in "${SERVICES[@]}"; do
        local container=$(get_container_name "$service")
        if [ -n "$container" ]; then
            # Truncate log file (requires appropriate permissions)
            docker exec "$container" sh -c 'echo "" > /proc/1/fd/1' 2>/dev/null || \
                log_warn "Could not truncate logs for $service (permission denied)"
        fi
    done
    
    # Clean local log files if they exist
    if [ -d "$LOG_DIR" ]; then
        log_info "Cleaning local log files older than 7 days..."
        find "$LOG_DIR" -name "*.log" -type f -mtime +7 -delete 2>/dev/null || true
    fi
    
    log_info "Log cleanup completed"
}

# Function to export logs
export_logs() {
    local service=${1:-}
    local timestamp=$(date +"%Y%m%d_%H%M%S")
    
    # Create logs directory if it doesn't exist
    mkdir -p "$LOG_DIR"
    
    if [ -n "$service" ]; then
        local output_file="$LOG_DIR/${service}_logs_${timestamp}.log"
        log_info "Exporting logs for service $service to: $output_file"
        docker-compose logs --no-color "$service" > "$output_file"
        log_info "Logs exported successfully"
    else
        local output_file="$LOG_DIR/all_logs_${timestamp}.log"
        log_info "Exporting logs for all services to: $output_file"
        docker-compose logs --no-color > "$output_file"
        log_info "Logs exported successfully"
    fi
    
    # Compress the log file
    gzip "$output_file" 2>/dev/null && \
        log_info "Log file compressed: ${output_file}.gz" || \
        log_warn "Could not compress log file"
}

# Parse command line arguments
COMMAND=""
SERVICE=""
LINES=100
SINCE=""

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_usage
            exit 0
            ;;
        -n|--lines)
            LINES="$2"
            shift 2
            ;;
        -s|--since)
            SINCE="$2"
            shift 2
            ;;
        tail|follow|errors|stats|clean|export)
            COMMAND="$1"
            shift
            ;;
        *)
            if [ -z "$SERVICE" ] && [[ " ${SERVICES[*]} " =~ " $1 " ]]; then
                SERVICE="$1"
            else
                log_error "Unknown argument: $1"
                show_usage
                exit 1
            fi
            shift
            ;;
    esac
done

# Default command
if [ -z "$COMMAND" ]; then
    COMMAND="tail"
fi

# Check prerequisites
check_docker_compose

# Execute command
case $COMMAND in
    tail)
        tail_logs "$SERVICE" "$LINES" "$SINCE"
        ;;
    follow)
        follow_logs "$SERVICE" "$LINES" "$SINCE"
        ;;
    errors)
        show_errors "$SERVICE" "$LINES" "$SINCE"
        ;;
    stats)
        show_stats
        ;;
    clean)
        clean_logs
        ;;
    export)
        export_logs "$SERVICE"
        ;;
    *)
        log_error "Unknown command: $COMMAND"
        show_usage
        exit 1
        ;;
esac