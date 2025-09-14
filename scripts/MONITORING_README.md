# Vogelring Monitoring & Alerting System

This directory contains comprehensive monitoring and alerting tools for the Vogelring application running on Raspberry Pi.

## Overview

The monitoring system provides:
- **Health Checks**: API endpoints and Docker service monitoring
- **Performance Monitoring**: System resources, response times, and database performance
- **Logging**: Centralized log management and analysis
- **Alerting**: Configurable alerts for critical issues
- **Resource Monitoring**: CPU, memory, disk, and temperature monitoring

## Quick Start

### Basic Monitoring

```bash
# Check current system status
./scripts/monitoring.sh status

# Continuous monitoring (updates every 30 seconds)
./scripts/monitoring.sh watch

# Check service health
./scripts/monitoring.sh health

# Show system resources
./scripts/monitoring.sh resources
```

### Log Management

```bash
# View recent logs for all services
./scripts/monitoring.sh logs

# Follow logs in real-time
./scripts/monitoring.sh follow api

# Show recent errors
./scripts/monitoring.sh errors

# Show log statistics
./scripts/monitoring.sh log-stats
```

### Alerting

```bash
# Run one-time alert check
./scripts/monitoring.sh alert-check

# Start alert daemon (checks every 5 minutes)
./scripts/monitoring.sh alert-daemon

# Test alert configuration
./scripts/monitoring.sh alert-test
```

## Components

### 1. Health Check Endpoints (`health.py`)

The FastAPI application includes comprehensive health check endpoints:

- `GET /health/` - Basic health check
- `GET /health/detailed` - Detailed health with system metrics
- `GET /health/ready` - Readiness check for container orchestration
- `GET /health/live` - Liveness check for container orchestration

### 2. System Monitor (`monitor.py`)

Python script that provides:
- Docker service status monitoring
- API health endpoint testing
- System resource monitoring (CPU, memory, disk, temperature)
- Database connectivity testing
- Comprehensive reporting in JSON or human-readable format

Usage:
```bash
python3 scripts/monitor.py                    # Single check
python3 scripts/monitor.py --json            # JSON output
python3 scripts/monitor.py --watch 60        # Monitor every 60 seconds
```

### 3. Log Monitor (`log_monitor.sh`)

Bash script for log management:
- View and follow logs for specific services
- Search for errors across all logs
- Export logs to files
- Clean old log files
- Show log statistics

Usage:
```bash
./scripts/log_monitor.sh tail api            # Show recent API logs
./scripts/log_monitor.sh follow postgres     # Follow PostgreSQL logs
./scripts/log_monitor.sh errors --lines 50   # Show last 50 error lines
./scripts/log_monitor.sh export api          # Export API logs to file
```

### 4. Alert System (`alert.py`)

Python-based alerting system with configurable thresholds:
- CPU usage monitoring
- Memory usage monitoring
- Disk usage monitoring
- Temperature monitoring (Raspberry Pi)
- API response time monitoring
- Email and webhook notifications
- Cooldown periods to prevent spam

Usage:
```bash
python3 scripts/alert.py                     # Single alert check
python3 scripts/alert.py --daemon            # Run as daemon
python3 scripts/alert.py --test              # Test configuration
```

### 5. Unified Monitoring Script (`monitoring.sh`)

Main entry point that provides access to all monitoring functions:
- System status and health checks
- Continuous monitoring
- Log management
- Alert management
- Maintenance operations

## Configuration

### Alert Configuration

Edit `scripts/alert_config.json` to configure alerting:

```json
{
  "thresholds": {
    "cpu_percent": 85,
    "memory_percent": 90,
    "disk_percent": 95,
    "temperature_celsius": 75,
    "response_time_ms": 5000
  },
  "cooldown_minutes": 30,
  "email": {
    "enabled": false,
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "username": "your-email@gmail.com",
    "password": "your-app-password",
    "from_email": "vogelring@yourdomain.com",
    "to_emails": ["admin@yourdomain.com"]
  },
  "webhook": {
    "enabled": false,
    "url": "https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK",
    "timeout": 10
  }
}
```

### Environment Variables

You can also configure alerts using environment variables:

```bash
export ALERT_CPU_THRESHOLD=80
export ALERT_MEMORY_THRESHOLD=85
export ALERT_EMAIL_ENABLED=true
export ALERT_EMAIL_FROM=vogelring@yourdomain.com
export ALERT_EMAIL_TO=admin@yourdomain.com
```

### Logging Configuration

The application uses structured logging with configurable levels:

```bash
export LOG_LEVEL=INFO                    # DEBUG, INFO, WARNING, ERROR
export LOG_FILE=./logs/vogelring.log     # Optional log file
export ENABLE_REQUEST_LOGGING=true       # Enable HTTP request logging
```

## Docker Health Checks

The Docker Compose configuration includes health checks for all services:

```yaml
# PostgreSQL health check
healthcheck:
  test: ["CMD-SHELL", "pg_isready -U vogelring -d vogelring"]
  interval: 30s
  timeout: 10s
  retries: 3

# API health check
healthcheck:
  test: ["CMD", "python", "-c", "import requests; requests.get('http://localhost:8000/health/ready', timeout=10)"]
  interval: 30s
  timeout: 10s
  retries: 3

# Nginx health check
healthcheck:
  test: ["CMD", "wget", "--quiet", "--tries=1", "--spider", "http://localhost/health"]
  interval: 30s
  timeout: 10s
  retries: 3
```

## Performance Optimizations

### Database Performance

The system includes several database performance optimizations:

1. **Connection Pooling**: Optimized for Raspberry Pi resources
2. **Indexes**: Case-insensitive indexes for autocomplete functionality
3. **Query Optimization**: Efficient queries with proper JOIN usage
4. **Caching**: In-memory caching for frequently accessed data

### System Resource Management

- **Memory Limits**: Docker containers have appropriate memory limits
- **CPU Limits**: CPU usage is constrained for stable operation
- **Connection Limits**: Database connections are pooled and limited

## Maintenance

### Regular Tasks

```bash
# Clean old logs and temporary files
./scripts/monitoring.sh cleanup

# Backup monitoring data
./scripts/monitoring.sh backup

# Restart services if needed
./scripts/monitoring.sh restart-services

# Update monitoring configuration
./scripts/monitoring.sh update-config
```

### Troubleshooting

1. **High Resource Usage**: Check `./scripts/monitoring.sh resources`
2. **Service Issues**: Check `./scripts/monitoring.sh health`
3. **Log Analysis**: Use `./scripts/monitoring.sh errors`
4. **Performance Issues**: Check `./scripts/monitoring.sh performance`

### Automated Monitoring

Set up automated monitoring with cron:

```bash
# Add to crontab (crontab -e)
# Check system every 5 minutes
*/5 * * * * /path/to/vogelring/scripts/alert.py --config /path/to/alert_config.json

# Daily cleanup
0 2 * * * /path/to/vogelring/scripts/monitoring.sh cleanup

# Weekly backup
0 3 * * 0 /path/to/vogelring/scripts/monitoring.sh backup
```

## Integration with External Systems

### Slack Integration

Configure webhook URL in alert configuration:

```json
{
  "webhook": {
    "enabled": true,
    "url": "https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK",
    "timeout": 10
  }
}
```

### Email Notifications

Configure SMTP settings for email alerts:

```json
{
  "email": {
    "enabled": true,
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "username": "your-email@gmail.com",
    "password": "your-app-password",
    "from_email": "vogelring@yourdomain.com",
    "to_emails": ["admin@yourdomain.com"]
  }
}
```

### Grafana/Prometheus Integration

The health endpoints provide metrics in a format suitable for Prometheus scraping:

```bash
# Prometheus can scrape these endpoints
curl http://localhost:8000/health/detailed
```

## Security Considerations

- **Log Rotation**: Logs are automatically rotated to prevent disk space issues
- **Sensitive Data**: Alert configurations may contain sensitive information (passwords, webhook URLs)
- **Access Control**: Monitoring endpoints should be protected in production environments
- **Resource Limits**: All containers have resource limits to prevent resource exhaustion

## Support

For issues with the monitoring system:

1. Check the logs: `./scripts/monitoring.sh logs`
2. Verify configuration: `./scripts/monitoring.sh alert-config`
3. Test connectivity: `./scripts/monitoring.sh health`
4. Check system resources: `./scripts/monitoring.sh resources`