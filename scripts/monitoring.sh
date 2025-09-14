#!/bin/bash
"""
Comprehensive monitoring script for Vogelring application
Provides easy access to all monitoring and alerting functions
"""

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
MONITOR_SCRIPT="$SCRIPT_DIR/monitor.py"
ALERT_SCRIPT="$SCRIPT_DIR/alert.py"
LOG_SCRIPT="$SCRIPT_DIR/log_monitor.sh"
ALERT_CONFIG="$SCRIPT_DIR/alert_config.json"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
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
${CYAN}Vogelring Monitoring & Alerting System${NC}

Usage: $0 [COMMAND] [OPTIONS]

${YELLOW}Monitoring Commands:${NC}
    status              Show current system status
    watch [INTERVAL]    Continuous monitoring (default: 30s)
    health              Check service health
    resources           Show system resources
    performance         Show performance metrics

${YELLOW}Log Commands:${NC}
    logs [SERVICE]      Show recent logs
    follow [SERVICE]    Follow logs in real-time
    errors [SERVICE]    Show recent errors
    log-stats           Show log statistics

${YELLOW}Alert Commands:${NC}
    alert-check         Run one-time alert check
    alert-daemon        Start alert daemon
    alert-test          Test alert configuration
    alert-config        Show alert configuration

${YELLOW}Maintenance Commands:${NC}
    cleanup             Clean old logs and temporary files
    backup              Backup monitoring data
    restart-services    Restart all services
    update-config       Update monitoring configuration

${YELLOW}Options:${NC}
    -h, --help         Show this help message
    -v, --verbose      Verbose output
    -j, --json         JSON output (where applicable)
    -c, --config FILE  Use custom alert configuration file

${YELLOW}Examples:${NC}
    $0 status                    # Show current status
    $0 watch 60                  # Monitor every 60 seconds
    $0 logs api                  # Show API logs
    $0 follow postgres           # Follow PostgreSQL logs
    $0 alert-daemon              # Start alert daemon
    $0 cleanup                   # Clean old files

${YELLOW}Services:${NC} postgres, api, nginx
EOF
}

# Function to check prerequisites
check_prerequisites() {
    local missing_deps=()
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        missing_deps+=("python3")
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        missing_deps+=("docker-compose")
    fi
    
    # Check required Python packages
    if ! python3 -c "import psutil, requests" &> /dev/null; then
        log_warn "Some Python packages may be missing (psutil, requests)"
    fi
    
    if [ ${#missing_deps[@]} -gt 0 ]; then
        log_error "Missing dependencies: ${missing_deps[*]}"
        log_error "Please install the missing dependencies and try again."
        exit 1
    fi
}

# Function to show system status
show_status() {
    local verbose=$1
    local json_output=$2
    
    log_info "Checking Vogelring system status..."
    
    if [ "$json_output" = "true" ]; then
        python3 "$MONITOR_SCRIPT" --json
    else
        python3 "$MONITOR_SCRIPT"
        
        if [ "$verbose" = "true" ]; then
            echo
            log_info "Docker service status:"
            docker-compose ps
        fi
    fi
}

# Function to start monitoring watch
start_watch() {
    local interval=${1:-30}
    local verbose=$2
    
    log_info "Starting continuous monitoring (interval: ${interval}s, press Ctrl+C to stop)"
    
    if [ "$verbose" = "true" ]; then
        python3 "$MONITOR_SCRIPT" --watch "$interval" --verbose
    else
        python3 "$MONITOR_SCRIPT" --watch "$interval"
    fi
}

# Function to check service health
check_health() {
    local verbose=$1
    
    log_info "Checking service health..."
    
    # Check Docker services
    echo "=== Docker Services ==="
    docker-compose ps
    
    echo
    echo "=== Health Endpoints ==="
    
    # Check API health endpoints
    local endpoints=("http://localhost:8000/health" "http://localhost:8000/health/ready" "http://localhost/health")
    
    for endpoint in "${endpoints[@]}"; do
        echo -n "Checking $endpoint: "
        if curl -s -f "$endpoint" > /dev/null 2>&1; then
            echo -e "${GREEN}OK${NC}"
        else
            echo -e "${RED}FAILED${NC}"
        fi
    done
    
    if [ "$verbose" = "true" ]; then
        echo
        echo "=== Detailed Health Check ==="
        curl -s "http://localhost:8000/health/detailed" | python3 -m json.tool 2>/dev/null || echo "Could not get detailed health info"
    fi
}

# Function to show system resources
show_resources() {
    log_info "System resource usage:"
    
    # CPU and memory
    if command -v htop &> /dev/null; then
        echo "Run 'htop' for interactive resource monitoring"
    fi
    
    echo "=== CPU Usage ==="
    if command -v mpstat &> /dev/null; then
        mpstat 1 1 | tail -1
    else
        echo "Install sysstat package for detailed CPU stats"
    fi
    
    echo
    echo "=== Memory Usage ==="
    free -h
    
    echo
    echo "=== Disk Usage ==="
    df -h /
    
    echo
    echo "=== Docker Resource Usage ==="
    docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}\t{{.NetIO}}\t{{.BlockIO}}"
    
    # Raspberry Pi specific
    if [ -f /sys/class/thermal/thermal_zone0/temp ]; then
        echo
        echo "=== Temperature ==="
        local temp=$(cat /sys/class/thermal/thermal_zone0/temp)
        echo "CPU Temperature: $((temp / 1000))°C"
    fi
}

# Function to show performance metrics
show_performance() {
    log_info "Performance metrics:"
    
    echo "=== API Response Times ==="
    local endpoints=("/" "/health" "/health/detailed" "/api/sightings" "/api/ringings")
    
    for endpoint in "${endpoints[@]}"; do
        echo -n "Testing http://localhost:8000$endpoint: "
        local response_time=$(curl -o /dev/null -s -w "%{time_total}" "http://localhost:8000$endpoint" 2>/dev/null || echo "failed")
        if [ "$response_time" != "failed" ]; then
            echo "${response_time}s"
        else
            echo -e "${RED}FAILED${NC}"
        fi
    done
    
    echo
    echo "=== Database Performance ==="
    # Simple database performance test via API
    echo -n "Database query test: "
    local start_time=$(date +%s.%N)
    if curl -s -f "http://localhost:8000/health/ready" > /dev/null 2>&1; then
        local end_time=$(date +%s.%N)
        local duration=$(echo "$end_time - $start_time" | bc -l 2>/dev/null || echo "unknown")
        echo "${duration}s"
    else
        echo -e "${RED}FAILED${NC}"
    fi
}

# Function to run alert check
run_alert_check() {
    local config_file=$1
    local verbose=$2
    
    log_info "Running alert check..."
    
    local args=()
    if [ -n "$config_file" ]; then
        args+=("--config" "$config_file")
    elif [ -f "$ALERT_CONFIG" ]; then
        args+=("--config" "$ALERT_CONFIG")
    fi
    
    if [ "$verbose" = "true" ]; then
        args+=("--verbose")
    fi
    
    python3 "$ALERT_SCRIPT" "${args[@]}"
}

# Function to start alert daemon
start_alert_daemon() {
    local config_file=$1
    local interval=${2:-300}
    
    log_info "Starting alert daemon (interval: ${interval}s)..."
    
    local args=("--daemon" "--interval" "$interval")
    if [ -n "$config_file" ]; then
        args+=("--config" "$config_file")
    elif [ -f "$ALERT_CONFIG" ]; then
        args+=("--config" "$ALERT_CONFIG")
    fi
    
    python3 "$ALERT_SCRIPT" "${args[@]}"
}

# Function to test alert configuration
test_alerts() {
    local config_file=$1
    
    log_info "Testing alert configuration..."
    
    local args=("--test")
    if [ -n "$config_file" ]; then
        args+=("--config" "$config_file")
    elif [ -f "$ALERT_CONFIG" ]; then
        args+=("--config" "$ALERT_CONFIG")
    fi
    
    python3 "$ALERT_SCRIPT" "${args[@]}"
}

# Function to show alert configuration
show_alert_config() {
    local config_file=${1:-$ALERT_CONFIG}
    
    if [ -f "$config_file" ]; then
        log_info "Alert configuration from: $config_file"
        cat "$config_file" | python3 -m json.tool
    else
        log_warn "Alert configuration file not found: $config_file"
        log_info "Create one using the template at: $ALERT_CONFIG"
    fi
}

# Function to cleanup old files
cleanup() {
    log_info "Cleaning up old files..."
    
    # Clean logs
    "$LOG_SCRIPT" clean
    
    # Clean monitoring state files
    find /tmp -name "vogelring_*" -type f -mtime +7 -delete 2>/dev/null || true
    
    # Clean Docker system
    log_info "Cleaning Docker system..."
    docker system prune -f
    
    log_info "Cleanup completed"
}

# Function to backup monitoring data
backup_monitoring_data() {
    local backup_dir="./backups/monitoring_$(date +%Y%m%d_%H%M%S)"
    
    log_info "Creating monitoring backup: $backup_dir"
    mkdir -p "$backup_dir"
    
    # Backup logs
    if [ -d "./logs" ]; then
        cp -r ./logs "$backup_dir/"
    fi
    
    # Backup configuration
    if [ -f "$ALERT_CONFIG" ]; then
        cp "$ALERT_CONFIG" "$backup_dir/"
    fi
    
    # Export current logs
    "$LOG_SCRIPT" export
    
    # Create system snapshot
    python3 "$MONITOR_SCRIPT" --json > "$backup_dir/system_snapshot.json"
    
    log_info "Backup created: $backup_dir"
}

# Function to restart services
restart_services() {
    log_info "Restarting Vogelring services..."
    
    cd "$PROJECT_ROOT"
    docker-compose restart
    
    # Wait for services to be ready
    log_info "Waiting for services to be ready..."
    sleep 10
    
    # Check health
    check_health false
}

# Function to update monitoring configuration
update_config() {
    log_info "Updating monitoring configuration..."
    
    # Create logs directory
    mkdir -p ./logs
    
    # Copy sample config if it doesn't exist
    if [ ! -f "$ALERT_CONFIG" ]; then
        log_info "Creating sample alert configuration..."
        # The config file should already exist from our creation above
    fi
    
    log_info "Configuration updated. Edit $ALERT_CONFIG to customize alerts."
}

# Parse command line arguments
COMMAND=""
VERBOSE=false
JSON_OUTPUT=false
CONFIG_FILE=""
INTERVAL=""

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_usage
            exit 0
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -j|--json)
            JSON_OUTPUT=true
            shift
            ;;
        -c|--config)
            CONFIG_FILE="$2"
            shift 2
            ;;
        status|watch|health|resources|performance|logs|follow|errors|log-stats|alert-check|alert-daemon|alert-test|alert-config|cleanup|backup|restart-services|update-config)
            COMMAND="$1"
            shift
            ;;
        *)
            # Check if it's an interval for watch command
            if [ "$COMMAND" = "watch" ] && [[ "$1" =~ ^[0-9]+$ ]]; then
                INTERVAL="$1"
            elif [ "$COMMAND" = "alert-daemon" ] && [[ "$1" =~ ^[0-9]+$ ]]; then
                INTERVAL="$1"
            else
                # Pass remaining arguments to log script
                break
            fi
            shift
            ;;
    esac
done

# Default command
if [ -z "$COMMAND" ]; then
    COMMAND="status"
fi

# Check prerequisites
check_prerequisites

# Change to project root
cd "$PROJECT_ROOT"

# Execute command
case $COMMAND in
    status)
        show_status "$VERBOSE" "$JSON_OUTPUT"
        ;;
    watch)
        start_watch "${INTERVAL:-30}" "$VERBOSE"
        ;;
    health)
        check_health "$VERBOSE"
        ;;
    resources)
        show_resources
        ;;
    performance)
        show_performance
        ;;
    logs|follow|errors|log-stats)
        "$LOG_SCRIPT" "$COMMAND" "$@"
        ;;
    alert-check)
        run_alert_check "$CONFIG_FILE" "$VERBOSE"
        ;;
    alert-daemon)
        start_alert_daemon "$CONFIG_FILE" "${INTERVAL:-300}"
        ;;
    alert-test)
        test_alerts "$CONFIG_FILE"
        ;;
    alert-config)
        show_alert_config "$CONFIG_FILE"
        ;;
    cleanup)
        cleanup
        ;;
    backup)
        backup_monitoring_data
        ;;
    restart-services)
        restart_services
        ;;
    update-config)
        update_config
        ;;
    *)
        log_error "Unknown command: $COMMAND"
        show_usage
        exit 1
        ;;
esac