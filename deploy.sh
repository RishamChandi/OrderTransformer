#!/bin/bash

# Order Transformation Platform Deployment Script

echo "🚀 Starting Order Transformation Platform deployment..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Stop any existing containers
echo "🛑 Stopping existing containers..."
docker-compose down

# Build and start services
echo "🔨 Building and starting services..."
docker-compose up --build -d

# Wait for database to be ready
echo "⏳ Waiting for database to initialize..."
sleep 10

# Initialize database
echo "🗄️ Initializing database..."
docker-compose exec app python init_database.py

echo "✅ Deployment complete!"
echo "📱 Application is running at: http://localhost:5000"
echo "🗄️ Database is running at: localhost:5432"
echo ""
echo "To view logs: docker-compose logs -f"
echo "To stop: docker-compose down"