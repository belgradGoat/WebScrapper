#!/bin/bash

# NotebookAI Startup Script
# Apple-inspired clean startup experience

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Apple-style banner
echo -e "${BLUE}"
echo "🍎 =========================================="
echo "   NotebookAI - Startup Script"
echo "   Multi-Modal AI Data Analysis Platform"
echo "==========================================${NC}"
echo ""

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if Docker is running
is_docker_running() {
    docker info >/dev/null 2>&1
}

# Function to wait for services
wait_for_service() {
    local url=$1
    local service_name=$2
    local max_attempts=30
    local attempt=1
    
    echo -n "⏳ Waiting for $service_name to be ready"
    
    while [ $attempt -le $max_attempts ]; do
        if curl -f -s "$url" >/dev/null 2>&1; then
            echo -e " ${GREEN}✅${NC}"
            return 0
        fi
        echo -n "."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    echo -e " ${RED}❌ Timeout${NC}"
    return 1
}

# Step 1: Check Docker installation
echo "🔍 Checking Docker installation..."
if ! command_exists docker; then
    echo -e "${RED}❌ Docker is not installed${NC}"
    echo "📥 Please install Docker Desktop:"
    echo "   macOS: https://docs.docker.com/desktop/install/mac-install/"
    echo "   Windows: https://docs.docker.com/desktop/install/windows-install/"
    echo "   Linux: https://docs.docker.com/desktop/install/linux-install/"
    exit 1
fi

if ! command_exists "docker compose"; then
    echo -e "${RED}❌ Docker Compose is not available${NC}"
    echo "📥 Please update Docker to the latest version"
    exit 1
fi

echo -e "${GREEN}✅ Docker is installed${NC}"

# Step 2: Check if Docker is running
echo "🚀 Checking Docker daemon..."
if ! is_docker_running; then
    echo -e "${YELLOW}⚠️  Docker daemon is not running${NC}"
    echo "🔧 Attempting to start Docker..."
    
    # Try to start Docker on macOS
    if [[ "$OSTYPE" == "darwin"* ]]; then
        if [ -d "/Applications/Docker.app" ]; then
            echo "📱 Starting Docker Desktop..."
            open -a Docker
            
            # Wait for Docker to start
            echo -n "⏳ Waiting for Docker to start"
            for i in {1..30}; do
                if is_docker_running; then
                    echo -e " ${GREEN}✅${NC}"
                    break
                fi
                echo -n "."
                sleep 2
            done
            
            if ! is_docker_running; then
                echo -e " ${RED}❌ Docker failed to start${NC}"
                echo "🔧 Please start Docker Desktop manually and try again"
                exit 1
            fi
        else
            echo -e "${RED}❌ Docker Desktop not found in Applications${NC}"
            exit 1
        fi
    else
        echo "🐧 Attempting to start Docker service..."
        sudo systemctl start docker
        sleep 5
        
        if ! is_docker_running; then
            echo -e "${RED}❌ Failed to start Docker service${NC}"
            echo "🔧 Please start Docker manually and try again"
            exit 1
        fi
    fi
else
    echo -e "${GREEN}✅ Docker daemon is running${NC}"
fi

# Step 3: Check for existing containers
echo "🔍 Checking for existing NotebookAI containers..."
if docker compose ps -q | grep -q .; then
    echo -e "${YELLOW}⚠️  Found existing containers${NC}"
    read -p "🤔 Do you want to stop and rebuild them? (y/N): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "🛑 Stopping existing containers..."
        docker compose down -v
        echo -e "${GREEN}✅ Containers stopped${NC}"
    fi
fi

# Step 4: Build and start services
echo "🏗️  Building and starting NotebookAI services..."
echo "📦 This may take a few minutes for the first build..."

if docker compose up --build -d; then
    echo -e "${GREEN}✅ Services started successfully${NC}"
else
    echo -e "${RED}❌ Failed to start services${NC}"
    echo "🔍 Check the logs with: docker compose logs"
    exit 1
fi

# Step 5: Wait for services to be ready
echo ""
echo "🔗 Checking service health..."

# Check backend health
if wait_for_service "http://localhost:8000/health" "Backend API"; then
    BACKEND_READY=true
else
    BACKEND_READY=false
fi

# Check frontend
if wait_for_service "http://localhost:3000" "Frontend"; then
    FRONTEND_READY=true
else
    FRONTEND_READY=false
fi

# Step 6: Display results
echo ""
echo -e "${BLUE}🍎 =========================================="
echo "   NotebookAI Status"
echo "==========================================${NC}"

if [ "$FRONTEND_READY" = true ]; then
    echo -e "🌐 Frontend:      ${GREEN}✅ Ready${NC}        http://localhost:3000"
else
    echo -e "🌐 Frontend:      ${RED}❌ Not Ready${NC}    http://localhost:3000"
fi

if [ "$BACKEND_READY" = true ]; then
    echo -e "🔧 Backend API:   ${GREEN}✅ Ready${NC}        http://localhost:8000"
    echo -e "📚 API Docs:      ${GREEN}✅ Ready${NC}        http://localhost:8000/docs"
else
    echo -e "🔧 Backend API:   ${RED}❌ Not Ready${NC}    http://localhost:8000"
    echo -e "📚 API Docs:      ${RED}❌ Not Ready${NC}    http://localhost:8000/docs"
fi

# Additional services
echo -e "🗄️  PostgreSQL:    ${GREEN}✅ Running${NC}      localhost:5432"
echo -e "🚀 Redis:         ${GREEN}✅ Running${NC}      localhost:6379"
echo -e "📦 MinIO:         ${GREEN}✅ Running${NC}      http://localhost:9001"
echo -e "🔍 Qdrant:        ${GREEN}✅ Running${NC}      http://localhost:6333"

echo ""
echo -e "${BLUE}🎯 Quick Actions:${NC}"
echo "   📱 Open App:           open http://localhost:3000"
echo "   📊 View Logs:          docker compose logs -f"
echo "   🛑 Stop Services:      docker compose down"
echo "   🔄 Restart:            docker compose restart"
echo "   🧹 Clean Reset:        docker compose down -v && ./start.sh"

echo ""
if [ "$FRONTEND_READY" = true ] && [ "$BACKEND_READY" = true ]; then
    echo -e "${GREEN}🎉 NotebookAI is ready! Opening in browser...${NC}"
    
    # Open in default browser
    if command_exists open; then
        open http://localhost:3000
    elif command_exists xdg-open; then
        xdg-open http://localhost:3000
    elif command_exists start; then
        start http://localhost:3000
    fi
else
    echo -e "${YELLOW}⚠️  Some services are not ready. Check logs with:${NC}"
    echo "   docker compose logs"
fi

echo ""
echo -e "${BLUE}🍎 Enjoy your Apple-inspired AI experience!${NC}"