# 🐳 NotebookAI Docker Setup Guide

## 📋 Prerequisites

### 1. Install Docker Desktop
**macOS:**
```bash
# Download Docker Desktop for Mac from: https://www.docker.com/products/docker-desktop
# Or install via Homebrew:
brew install --cask docker
```

**Windows:**
- Download Docker Desktop for Windows from: https://www.docker.com/products/docker-desktop
- Follow the installation wizard

**Linux (Ubuntu/Debian):**
```bash
# Update package index
sudo apt-get update

# Install Docker
sudo apt-get install docker.io docker-compose-plugin

# Add user to docker group
sudo usermod -aG docker $USER

# Start Docker service
sudo systemctl start docker
sudo systemctl enable docker

# Log out and log back in for group changes to take effect
```

### 2. Verify Docker Installation
```bash
# Check Docker version
docker --version

# Check Docker Compose version  
docker compose version

# Test Docker installation
docker run hello-world
```

## 🚀 Quick Start (One Command Setup)

### 1. Navigate to Project Directory
```bash
cd /Users/sebastianszewczyk/Documents/GitHub/WebScrapper/notebookai
```

### 2. Start All Services
```bash
# Build and start all services
docker compose up --build

# Or run in background (detached mode)
docker compose up --build -d
```

### 3. Access NotebookAI
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **MinIO Console**: http://localhost:9001 (admin/minioadmin)
- **Qdrant Dashboard**: http://localhost:6333/dashboard

## 🏗️ Service Architecture

### Services Overview
- **frontend**: React application (port 3000)
- **backend**: FastAPI application (port 8000)  
- **worker**: Celery background tasks
- **postgres**: PostgreSQL database (port 5432)
- **redis**: Redis cache & message broker (port 6379)
- **minio**: Object storage (ports 9000/9001)
- **qdrant**: Vector database (port 6333)

### Service Dependencies
```
frontend → backend → postgres, redis, minio, qdrant
worker → postgres, redis, minio
```

## 🔧 Development Workflow

### 1. Start Services for Development
```bash
# Start with live reload (for development)
docker compose up --build

# View logs from all services
docker compose logs -f

# View logs from specific service
docker compose logs -f backend
docker compose logs -f frontend
```

### 2. Stop Services
```bash
# Stop all services
docker compose down

# Stop and remove volumes (clean slate)
docker compose down -v

# Stop and remove everything including images
docker compose down -v --rmi all
```

### 3. Rebuild Specific Services
```bash
# Rebuild and restart backend only
docker compose up --build backend

# Rebuild frontend only
docker compose up --build frontend
```

## 🗄️ Database Management

### 1. Access PostgreSQL Database
```bash
# Connect to PostgreSQL container
docker compose exec postgres psql -U notebookai -d notebookai_db

# Or from host machine (if you have psql installed)
psql -h localhost -p 5432 -U notebookai -d notebookai_db
```

### 2. Database Operations
```sql
-- Inside PostgreSQL shell
\l                          -- List databases
\c notebookai_db           -- Connect to database
\dt                        -- List tables
\d users                   -- Describe users table
SELECT * FROM users;       -- Query users
```

### 3. Reset Database
```bash
# Stop services and remove volumes
docker compose down -v

# Restart services (will recreate database)
docker compose up --build
```

## 📦 Container Management

### 1. View Running Containers
```bash
# List running containers
docker ps

# List all containers (including stopped)
docker ps -a

# View container resource usage
docker stats
```

### 2. Execute Commands in Containers
```bash
# Access backend container shell
docker compose exec backend bash

# Access frontend container shell  
docker compose exec frontend sh

# Run database migrations
docker compose exec backend python -c "from app.core.database import create_tables; import asyncio; asyncio.run(create_tables())"

# Install new Python package
docker compose exec backend pip install new-package
```

### 3. View Container Logs
```bash
# All services logs
docker compose logs

# Specific service logs
docker compose logs backend
docker compose logs frontend

# Follow logs in real-time
docker compose logs -f backend

# Last 100 lines
docker compose logs --tail=100 backend
```

## 🔍 Troubleshooting

### Common Issues and Solutions

#### 1. Port Already in Use
```bash
# Check what's using the port
lsof -i :3000
lsof -i :8000

# Kill process using port
kill -9 $(lsof -t -i:3000)

# Or change ports in docker-compose.yml
ports:
  - "3001:3000"  # Use port 3001 instead
```

#### 2. Docker Daemon Not Running
```bash
# Start Docker Desktop application
open /Applications/Docker.app

# Or start Docker service (Linux)
sudo systemctl start docker
```

#### 3. Permission Denied Errors
```bash
# Fix Docker permissions (Linux)
sudo chmod 666 /var/run/docker.sock

# Or add user to docker group
sudo usermod -aG docker $USER
# Then log out and log back in
```

#### 4. Container Build Failures
```bash
# Clean Docker cache
docker system prune -a

# Rebuild without cache
docker compose build --no-cache

# Remove all containers and rebuild
docker compose down -v
docker compose up --build
```

#### 5. Database Connection Issues
```bash
# Check if PostgreSQL container is running
docker compose ps postgres

# View PostgreSQL logs
docker compose logs postgres

# Reset database completely
docker compose down -v
docker volume rm notebookai_postgres_data
docker compose up --build
```

#### 6. Frontend Build Issues
```bash
# Clear npm cache in container
docker compose exec frontend npm cache clean --force

# Rebuild frontend
docker compose build --no-cache frontend
docker compose up frontend
```

## ⚙️ Configuration

### 1. Environment Variables
Create `.env` file in the root directory:
```bash
# Copy example environment file
cp backend/.env.example .env

# Edit configuration
nano .env
```

### 2. Custom Configuration
Edit `docker-compose.yml` to customize:
- Port mappings
- Environment variables
- Volume mounts
- Resource limits

Example customization:
```yaml
services:
  backend:
    environment:
      - OPENAI_API_KEY=your-key-here
      - DEBUG=false
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: '0.5'
```

## 🚀 Production Deployment

### 1. Production Build
```bash
# Build for production
docker compose -f docker-compose.yml build

# Use production environment
docker compose --env-file .env.production up -d
```

### 2. Security Considerations
- Change default passwords in production
- Use proper SSL certificates
- Set up firewall rules
- Enable Docker security scanning
- Use secrets management

### 3. Monitoring
```bash
# View container resource usage
docker stats

# Export logs for monitoring
docker compose logs > notebookai.log

# Health checks
curl http://localhost:8000/health
curl http://localhost:3000
```

## 🧹 Cleanup

### 1. Remove All NotebookAI Containers
```bash
# Stop and remove containers
docker compose down

# Remove containers and volumes
docker compose down -v

# Remove containers, volumes, and images
docker compose down -v --rmi all
```

### 2. Clean Docker System
```bash
# Remove unused containers, networks, images
docker system prune

# Remove everything (be careful!)
docker system prune -a --volumes
```

## 📚 Additional Resources

- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Docker Desktop Documentation](https://docs.docker.com/desktop/)
- [FastAPI Docker Documentation](https://fastapi.tiangolo.com/deployment/docker/)
- [React Docker Documentation](https://create-react-app.dev/docs/deployment/#docker)

## 🆘 Getting Help

If you encounter issues:

1. **Check the logs**: `docker compose logs [service-name]`
2. **Restart services**: `docker compose restart [service-name]`
3. **Clean rebuild**: `docker compose down -v && docker compose up --build`
4. **Check Docker status**: `docker system info`
5. **Free up space**: `docker system prune`

Your NotebookAI application should now be running with the beautiful Apple-inspired interface at http://localhost:3000!