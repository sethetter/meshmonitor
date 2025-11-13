#!/bin/bash
# Simple script to run Meshtastic MQTT Monitor with Docker Compose

set -e

echo "========================================"
echo "Meshtastic MQTT Monitor - Docker Setup"
echo "========================================"

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed"
    echo "Please install Docker: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "Error: Docker Compose is not installed"
    echo "Please install Docker Compose: https://docs.docker.com/compose/install/"
    exit 1
fi

# Create necessary directories
echo "Creating required directories..."
mkdir -p data
mkdir -p mosquitto/data
mkdir -p mosquitto/log

# Set proper permissions
chmod 755 data mosquitto/data mosquitto/log

# Check if .env file exists, if not create from example
if [ ! -f .env ]; then
    if [ -f .env.example ]; then
        echo "Creating .env file from .env.example..."
        cp .env.example .env
        echo "Please edit .env file with your configuration"
    fi
fi

# Determine which compose command to use
if command -v docker-compose &> /dev/null; then
    COMPOSE_CMD="docker-compose"
else
    COMPOSE_CMD="docker compose"
fi

# Parse command line arguments
COMMAND=${1:-up}

case $COMMAND in
    up)
        echo "Starting Meshtastic MQTT Monitor..."
        $COMPOSE_CMD up -d
        echo ""
        echo "========================================"
        echo "Meshtastic MQTT Monitor is running!"
        echo "========================================"
        echo "Web Interface: http://localhost:8080"
        echo "MQTT Broker: localhost:1883 (internal)"
        echo "MQTT Broker: localhost:8883 (external)"
        echo "WebSocket: ws://localhost:9001"
        echo ""
        echo "To view logs: $COMPOSE_CMD logs -f"
        echo "To stop: $COMPOSE_CMD down"
        echo "========================================"
        ;;
    down)
        echo "Stopping Meshtastic MQTT Monitor..."
        $COMPOSE_CMD down
        ;;
    logs)
        $COMPOSE_CMD logs -f
        ;;
    restart)
        echo "Restarting Meshtastic MQTT Monitor..."
        $COMPOSE_CMD restart
        ;;
    build)
        echo "Building Docker images..."
        $COMPOSE_CMD build
        ;;
    pull)
        echo "Pulling latest images..."
        $COMPOSE_CMD pull
        ;;
    *)
        echo "Usage: $0 {up|down|logs|restart|build|pull}"
        echo ""
        echo "Commands:"
        echo "  up       - Start the application"
        echo "  down     - Stop the application"
        echo "  logs     - View application logs"
        echo "  restart  - Restart the application"
        echo "  build    - Rebuild Docker images"
        echo "  pull     - Pull latest base images"
        exit 1
        ;;
esac
