#!/bin/bash

# QuikScribe Backend Docker Quick Start Script

echo "🐳 Starting QuikScribe Backend with Docker..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Resolve Docker Compose command (support v2 and v1)
if docker compose version > /dev/null 2>&1; then
    COMPOSE="docker compose"
elif command -v docker-compose > /dev/null 2>&1; then
    COMPOSE="docker-compose"
else
    echo "❌ Docker Compose is not installed. Install Docker Compose v2 or v1."
    echo "   - For v2: comes with recent Docker as 'docker compose'"
    echo "   - For v1: install standalone 'docker-compose' binary"
    exit 1
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp env.template .env
    echo "⚠️  Please edit .env file with your actual values before continuing."
    echo "   You can edit it now or continue and edit it later."
    read -p "   Continue anyway? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "❌ Setup cancelled. Please edit .env file and run again."
        exit 1
    fi
fi

# Check if ports are available
echo "🔍 Checking if required ports are available..."

check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo "❌ Port $port is already in use. Please free up port $port first."
        exit 1
    fi
}

check_port 8000
check_port 3000
check_port 5432
check_port 6379

echo "✅ All ports are available."

# Build and start services
echo "🚀 Building and starting services..."
$COMPOSE up --build -d

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 10

# Check service health
echo "🔍 Checking service health..."

# Check backend health
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Backend API is healthy"
else
    echo "⚠️  Backend API health check failed (may still be starting)"
fi

# Check PostgreSQL
if $COMPOSE exec -T postgres pg_isready -U quikscribe_user -d quikscribe > /dev/null 2>&1; then
    echo "✅ PostgreSQL is ready"
else
    echo "⚠️  PostgreSQL may still be starting"
fi

# Check Redis
if $COMPOSE exec -T redis redis-cli ping > /dev/null 2>&1; then
    echo "✅ Redis is ready"
else
    echo "⚠️  Redis may still be starting"
fi

echo ""
echo "🎉 QuikScribe Backend is starting up!"
echo ""
echo "📊 Service Status:"
echo "   Backend API: http://localhost:8000"
echo "   API Docs:   http://localhost:8000/docs"
echo "   Google Bot: http://localhost:3000"
echo "   PostgreSQL: localhost:5432"
echo "   Redis:      localhost:6379"
echo ""
echo "📝 Useful Commands:"
echo "   View logs:        $COMPOSE logs -f"
echo "   Stop services:    $COMPOSE down"
echo "   Restart:          $COMPOSE restart"
echo "   Status:           $COMPOSE ps"
echo ""
echo "🔧 Next Steps:"
echo "   1. Wait a few more seconds for all services to fully start"
echo "   2. Visit http://localhost:8000/docs to see your API documentation"
echo "   3. Edit .env file with your actual configuration values"
echo "   4. Start developing!"
echo ""
echo "💡 Tip: Run '$COMPOSE logs -f' to see real-time logs from all services."
