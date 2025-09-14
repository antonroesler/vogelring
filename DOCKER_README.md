# Vogelring Docker Deployment Guide

This guide covers the Docker-based deployment of the Vogelring bird tracking application on Raspberry Pi 5.

## Prerequisites

- Raspberry Pi 5 with Raspberry Pi OS (64-bit recommended)
- Docker and Docker Compose installed
- At least 4GB RAM (8GB recommended)
- 32GB+ SD card or SSD storage
- Internet connection for initial setup

## Quick Start

1. **Clone the repository and navigate to the project directory**
   ```bash
   git clone <repository-url>
   cd vogelring
   ```

2. **Configure environment variables**
   ```bash
   cp .env.example .env
   nano .env  # Edit with your configuration
   ```

3. **Deploy the application**
   ```bash
   ./scripts/deploy.sh
   ```

4. **Access the application**
   - Frontend: http://localhost
   - API: http://localhost:8000
   - API Documentation: http://localhost:8000/swagger

## Architecture

The application consists of three main services:

- **PostgreSQL Database**: Stores all bird ringing and sighting data
- **FastAPI Backend**: Provides REST API endpoints
- **Nginx Reverse Proxy**: Serves frontend and routes API requests

## Configuration

### Environment Variables

Edit the `.env` file to configure your deployment:

```bash
# Database Configuration
DB_PASSWORD=your_secure_password_here
DB_PORT=5432

# API Configuration
API_PORT=8000
LOG_LEVEL=INFO

# Web Server Configuration
HTTP_PORT=80

# Data Directory
DATA_DIR=./data
```

### Resource Limits

The Docker Compose configuration includes resource limits optimized for Raspberry Pi:

- **PostgreSQL**: 512MB RAM limit, optimized configuration
- **FastAPI**: 512MB RAM limit, single worker process
- **Nginx**: 128MB RAM limit, efficient caching

## Data Management

### Backup

Create a backup of your data:
```bash
./scripts/backup.sh
```

Backups are stored in `./data/backups/` and include:
- Database dump (compressed)
- Complete data directory archive

### Restore

Restore from a backup:
```bash
./scripts/restore.sh latest                    # Restore latest backup
./scripts/restore.sh vogelring_20240312.sql.gz # Restore specific backup
```

### Data Migration

If migrating from AWS, use the migration scripts in `scripts/migration/`:
```bash
cd scripts/migration
./run_migration.sh
```

## Maintenance

### Update Application

Update to the latest version:
```bash
./scripts/update.sh
```

### View Logs

Monitor application logs:
```bash
docker-compose logs -f          # All services
docker-compose logs -f api      # API only
docker-compose logs -f postgres # Database only
```

### Service Management

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# Restart services
docker-compose restart

# Check service status
docker-compose ps

# Check service health
docker-compose exec api curl http://localhost:8000/health
```

## Performance Optimization

### Database Tuning

The PostgreSQL configuration is optimized for Raspberry Pi in `postgres.conf`:
- Shared buffers: 128MB
- Effective cache size: 256MB
- Connection limit: 20

### Monitoring

Monitor resource usage:
```bash
# System resources
htop

# Docker container resources
docker stats

# Disk usage
df -h
du -sh ./data/
```

## Troubleshooting

### Common Issues

1. **Services fail to start**
   ```bash
   # Check logs
   docker-compose logs
   
   # Check disk space
   df -h
   
   # Check memory usage
   free -h
   ```

2. **Database connection errors**
   ```bash
   # Check database health
   docker-compose exec postgres pg_isready -U vogelring
   
   # Restart database
   docker-compose restart postgres
   ```

3. **API health check failures**
   ```bash
   # Check API logs
   docker-compose logs api
   
   # Test API directly
   curl http://localhost:8000/health
   ```

4. **Frontend not loading**
   ```bash
   # Check nginx logs
   docker-compose logs nginx
   
   # Verify frontend files
   ls -la frontend/dist/
   ```

### Performance Issues

1. **Slow database queries**
   - Check database indexes
   - Monitor query performance in logs
   - Consider increasing shared_buffers if RAM allows

2. **High memory usage**
   - Monitor with `docker stats`
   - Adjust resource limits in docker-compose.yml
   - Consider reducing worker processes

3. **Storage issues**
   - Monitor disk usage: `df -h`
   - Clean old logs: `docker system prune`
   - Archive old backups

## Security Considerations

### Network Security
- Services communicate via internal Docker network
- Only necessary ports are exposed
- Nginx handles all external requests

### Data Security
- Database password should be strong and unique
- Regular backups are encrypted and stored securely
- Consider using Docker secrets for production

### Updates
- Regularly update base images
- Monitor security advisories
- Keep host system updated

## Development Mode

For development, uncomment the volume mount in docker-compose.yml:
```yaml
api:
  volumes:
    - ./backend/src:/app/src  # Enables hot reload
```

## Production Deployment

For production deployment:

1. **Remove development volume mounts**
2. **Use strong passwords**
3. **Configure proper logging**
4. **Set up monitoring**
5. **Configure automated backups**
6. **Use HTTPS with proper certificates**

## Support

For issues and questions:
1. Check the logs: `docker-compose logs`
2. Review this documentation
3. Check GitHub issues
4. Create a new issue with logs and system information

## File Structure

```
vogelring/
├── backend/
│   ├── Dockerfile              # FastAPI container definition
│   ├── requirements.txt        # Python dependencies
│   └── src/                   # Application source code
├── frontend/
│   └── dist/                  # Built Vue.js application
├── nginx/
│   └── nginx.conf             # Nginx configuration
├── scripts/
│   ├── deploy.sh              # Deployment script
│   ├── update.sh              # Update script
│   ├── backup.sh              # Backup script
│   └── restore.sh             # Restore script
├── docker-compose.yml         # Service orchestration
├── postgres.conf              # PostgreSQL configuration
├── .env.example               # Environment template
└── data/                      # Persistent data directory
    ├── postgres/              # Database files
    └── backups/               # Backup files
```