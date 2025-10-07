# 🐳 Docker Setup Guide for QuikScribe Backend

This guide will help you dockerize and run your QuikScribe backend project for development and testing.

## 📁 What We're Dockerizing

### 1. **Main Backend API** (Root Directory)
- FastAPI application with SQLAlchemy
- Authentication and authorization
- Database models and migrations
- API endpoints

### 2. **Google Bot Service** (google_bot/ folder)
- TypeScript/Node.js service
- Google Meet integration
- AWS S3 integration

## 🚀 Quick Start

### Prerequisites
- Docker installed
- Docker Compose installed
- Ports 8000, 3000, 5432, 6379 available

### 1. Build and Run Everything
```bash
# Make sure you're in the project root
cd /home/voidraghav/Desktop/Quikscribe-AWS/backend-quikscribe

# Build and start all services
docker-compose up --build
```

### 2. Access Your Services
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Google Bot**: http://localhost:3000
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379

## 🔧 Individual Service Commands

### Backend Only
```bash
# Build backend image
docker build -t quikscribe-backend .

# Run backend container
docker run -p 8000:8000 --env-file .env quikscribe-backend
```

### Database Only
```bash
# Start just PostgreSQL
docker-compose up postgres

# Start just Redis
docker-compose up redis
```

### Google Bot Only
```bash
# Build and run Google Bot
cd google_bot
docker build -t quikscribe-google-bot .
docker run -p 3000:3000 quikscribe-google-bot
```

## 📊 Service Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend API   │    │   Google Bot    │
│   (Port 3000)   │◄──►│   (Port 8000)   │◄──►│   (Port 3000)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │   PostgreSQL    │
                       │   (Port 5432)   │
                       └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │     Redis       │
                       │   (Port 6379)   │
                       └─────────────────┘
```

## 🛠️ Development Workflow

### 1. Start Development Environment
```bash
# Start all services in background
docker-compose up -d

# View logs
docker-compose logs -f backend
docker-compose logs -f google_bot
```

### 2. Make Code Changes
- Edit files in your local directory
- Changes are automatically reflected due to volume mounts
- Backend will auto-reload (if DEBUG=true)

### 3. Test Your Changes
```bash
# Test backend health
curl http://localhost:8000/health

# Test API endpoints
curl http://localhost:8000/api/v1/

# View API documentation
open http://localhost:8000/docs
```

### 4. Database Operations
```bash
# Connect to PostgreSQL
docker exec -it quikscribe_postgres psql -U quikscribe_user -d quikscribe

# Run migrations (if using Alembic)
docker exec -it quikscribe_backend alembic upgrade head
```

## 🔍 Troubleshooting

### Common Issues

#### 1. Port Already in Use
```bash
# Check what's using the port
sudo lsof -i :8000
sudo lsof -i :5432

# Kill the process or change ports in docker-compose.yml
```

#### 2. Database Connection Issues
```bash
# Check if PostgreSQL is running
docker-compose ps postgres

# Check PostgreSQL logs
docker-compose logs postgres

# Restart PostgreSQL
docker-compose restart postgres
```

#### 3. Backend Won't Start
```bash
# Check backend logs
docker-compose logs backend

# Check if dependencies are installed
docker exec -it quikscribe_backend pip list

# Rebuild backend
docker-compose build --no-cache backend
```

#### 4. Permission Issues
```bash
# Fix file permissions
sudo chown -R $USER:$USER .

# Or run with proper user in Docker
```

### Debug Commands
```bash
# Enter running container
docker exec -it quikscribe_backend bash

# Check container resources
docker stats

# View container details
docker inspect quikscribe_backend

# Check network connectivity
docker network ls
docker network inspect quikscribe_quikscribe_network
```

## 🚀 Production Considerations

### 1. Environment Variables
```bash
# Create production .env file
cp .env.example .env.production

# Edit with production values
nano .env.production

# Use production environment
docker-compose --env-file .env.production up -d
```

### 2. Security
- Change default passwords
- Use strong SECRET_KEY
- Restrict network access
- Enable SSL/TLS

### 3. Performance
- Use production PostgreSQL settings
- Configure Redis for production
- Set appropriate resource limits
- Enable logging aggregation

## 📝 Useful Commands

### Development
```bash
# Start all services
docker-compose up

# Start in background
docker-compose up -d

# View logs
docker-compose logs -f

# Stop all services
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

### Maintenance
```bash
# Clean up unused images
docker image prune

# Clean up unused containers
docker container prune

# Clean up everything
docker system prune -a

# Update images
docker-compose pull
```

### Monitoring
```bash
# View running containers
docker-compose ps

# View resource usage
docker stats

# Check service health
curl http://localhost:8000/health
```

## 🎯 Next Steps

1. **Test the setup**: Run `docker-compose up --build`
2. **Verify all services**: Check health endpoints
3. **Run your tests**: Execute test suite
4. **Configure environment**: Set up your .env file
5. **Start development**: Begin coding with hot-reload

## 📚 Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [FastAPI Docker Guide](https://fastapi.tiangolo.com/deployment/docker/)
- [PostgreSQL Docker](https://hub.docker.com/_/postgres)
- [Redis Docker](https://hub.docker.com/_/redis)

---

🎉 **You're all set!** Your QuikScribe backend is now fully dockerized and ready for development and testing.
