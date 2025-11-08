#!/bin/bash
# Start Amalfi Events system in Docker

set -e

echo "🚀 Starting Amalfi Events Intelligence System in Docker"

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚠️  Warning: .env file not found"
    echo "📝 Creating from .env.example..."
    cp .env.example .env
    echo "✏️  Please edit .env with your API keys before continuing"
    exit 1
fi

# Build and start container
echo "🔨 Building Docker image..."
docker-compose build

echo "🚀 Starting container..."
docker-compose up -d

# Wait for container to be healthy
echo "⏳ Waiting for container to be healthy..."
sleep 5

# Get the assigned port
PORT=$(docker-compose port amalfi-events 8000 | cut -d: -f2)

if [ -z "$PORT" ]; then
    echo "❌ Failed to get assigned port"
    docker-compose logs
    exit 1
fi

echo ""
echo "✅ Amalfi Events system is running!"
echo ""
echo "📊 Web Interface: http://localhost:$PORT"
echo "📚 API Docs: http://localhost:$PORT/docs"
echo "📈 Status: http://localhost:$PORT/status"
echo ""
echo "🔍 View logs: docker-compose logs -f"
echo "🛑 Stop: docker-compose stop"
echo "⚙️  Shell: docker-compose exec amalfi-events bash"
echo ""
