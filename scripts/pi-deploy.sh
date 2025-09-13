#!/bin/bash

# Pi Deployment Script
# Run this on the Raspberry Pi after pushing changes to git
# Usage: ./scripts/pi-deploy.sh [--prod] [--no-backup] [--force]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
COMPOSE_FILE="docker-compose.yml"
ENV_FILE=".env"
BACKUP_BEFORE_DEPLOY=true
FORCE_DEPLOY=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --prod)
            COMPOSE_FILE="docker-compose.prod.yml"
            ENV_FILE=".env.production"
            shift
            ;;
        --no-backup)
            BACKUP_BEFORE_DEPLOY=false
            shift
            ;;
        --force)
            FORCE_DEPLOY=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --prod        Use production compose file and environment"
            echo "  --no-backup   Skip database backup before deployment"
            echo "  --force       Skip confirmation prompt"
            echo "  -h, --help    Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

echo -e "${BLUE}🚀 Starting Pi deployment...${NC}"
echo -e "   Compose file: ${COMPOSE_FILE}"
echo -e "   Environment: ${ENV_FILE}"
echo -e "   Backup before deploy: ${BACKUP_BEFORE_DEPLOY}"

# Confirmation prompt (unless --force is used)
if [ "$FORCE_DEPLOY" != "true" ]; then
    echo ""
    read -p "Continue with deployment? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}❌ Deployment cancelled${NC}"
        exit 1
    fi
fi

# Check if we're in the right directory
if [ ! -f "docker-compose.yml" ] || [ ! -f "docker-compose.prod.yml" ]; then
    echo -e "${RED}❌ Error: Not in vogelring project directory${NC}"
    echo "Please run this script from the project root directory"
    exit 1
fi

# Check if environment file exists
if [ ! -f "$ENV_FILE" ]; then
    echo -e "${RED}❌ Error: Environment file $ENV_FILE not found${NC}"
    exit 1
fi

# Step 1: Pull latest code
echo -e "${BLUE}📥 Pulling latest code from git...${NC}"
git fetch origin
CURRENT_BRANCH=$(git branch --show-current)
echo -e "   Current branch: ${CURRENT_BRANCH}"

# Check if there are updates
BEHIND=$(git rev-list HEAD..origin/${CURRENT_BRANCH} --count 2>/dev/null || echo "0")
if [ "$BEHIND" -eq 0 ]; then
    echo -e "${GREEN}✅ Already up to date${NC}"
else
    echo -e "${YELLOW}📦 Pulling $BEHIND new commits...${NC}"
    git pull origin "$CURRENT_BRANCH"
fi

# Step 2: Backup database (if enabled and services are running)
if [ "$BACKUP_BEFORE_DEPLOY" = "true" ]; then
    echo -e "${BLUE}💾 Creating backup before deployment...${NC}"
    if docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" ps postgres | grep -q "Up"; then
        if [ -f "./scripts/backup.sh" ]; then
            # Set DATA_DIR if using production
            if [ "$COMPOSE_FILE" = "docker-compose.prod.yml" ]; then
                DATA_DIR=/mnt/ssd/data/vogelring ./scripts/backup.sh
            else
                ./scripts/backup.sh
            fi
            echo -e "${GREEN}✅ Backup completed${NC}"
        else
            echo -e "${YELLOW}⚠️  Backup script not found, skipping backup${NC}"
        fi
    else
        echo -e "${YELLOW}⚠️  Database not running, skipping backup${NC}"
    fi
fi

# Step 3: Stop services gracefully
echo -e "${BLUE}🛑 Stopping services...${NC}"
docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" down

# Step 4: Build updated images
echo -e "${BLUE}🔨 Building updated images...${NC}"
docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" build --no-cache

# Step 5: Start services
echo -e "${BLUE}🚀 Starting services...${NC}"
docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d

# Step 6: Wait for services to be healthy
echo -e "${BLUE}⏳ Waiting for services to be healthy...${NC}"
TIMEOUT=120
COUNTER=0

while [ $COUNTER -lt $TIMEOUT ]; do
    # Check if all services are healthy or running
    UNHEALTHY=$(docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" ps --format json | jq -r '.[] | select(.Health != "healthy" and .Health != "" and .State != "running") | .Name' 2>/dev/null | wc -l || echo "0")
    
    if [ "$UNHEALTHY" -eq 0 ]; then
        echo -e "${GREEN}✅ All services are healthy${NC}"
        break
    fi
    
    echo -e "${YELLOW}   Waiting... ($((TIMEOUT - COUNTER))s remaining)${NC}"
    sleep 5
    COUNTER=$((COUNTER + 5))
done

if [ $COUNTER -ge $TIMEOUT ]; then
    echo -e "${RED}⚠️  Timeout waiting for services to be healthy${NC}"
    echo -e "${YELLOW}   Check service status manually:${NC}"
    echo -e "   docker compose -f $COMPOSE_FILE --env-file $ENV_FILE ps"
    echo -e "   docker compose -f $COMPOSE_FILE --env-file $ENV_FILE logs"
fi

# Step 7: Display service status
echo -e "${BLUE}📊 Final service status:${NC}"
docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" ps

# Step 8: Test API endpoint (if available)
if [ "$COMPOSE_FILE" = "docker-compose.prod.yml" ]; then
    API_URL="http://localhost:8000"
else
    API_URL="http://localhost:${API_PORT:-8000}"
fi

echo -e "${BLUE}🔍 Testing API health...${NC}"
if curl -f -s "$API_URL/health" > /dev/null; then
    echo -e "${GREEN}✅ API is responding${NC}"
    echo -e "   Health endpoint: $API_URL/health"
    echo -e "   API docs: $API_URL/swagger"
else
    echo -e "${YELLOW}⚠️  API health check failed${NC}"
    echo -e "   Check API logs: docker compose -f $COMPOSE_FILE --env-file $ENV_FILE logs api"
fi

# Step 9: Clean up old Docker images
echo -e "${BLUE}🧹 Cleaning up old Docker images...${NC}"
docker image prune -f > /dev/null 2>&1 || true

echo ""
echo -e "${GREEN}🎉 Deployment completed!${NC}"
echo -e "${BLUE}📋 Quick commands:${NC}"
echo -e "   View logs: docker compose -f $COMPOSE_FILE --env-file $ENV_FILE logs -f"
echo -e "   Check status: docker compose -f $COMPOSE_FILE --env-file $ENV_FILE ps"
echo -e "   Stop services: docker compose -f $COMPOSE_FILE --env-file $ENV_FILE down"

if [ "$COMPOSE_FILE" = "docker-compose.prod.yml" ]; then
    echo -e "${BLUE}🌐 Production URLs:${NC}"
    echo -e "   Frontend: https://vogelring.com (via Cloudflare tunnel)"
    echo -e "   API: https://vogelring.com/api"
else
    echo -e "${BLUE}🌐 Development URLs:${NC}"
    echo -e "   Frontend: http://localhost"
    echo -e "   API: http://localhost:${API_PORT:-8000}"
fi
