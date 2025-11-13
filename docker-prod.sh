#!/bin/bash
# Production deployment script for Meshtastic MQTT Monitor with Docker

set -e

echo "================================================"
echo "Meshtastic MQTT Monitor - Production Deployment"
echo "================================================"

# Check if running as root or with sudo
if [ "$EUID" -ne 0 ]; then
    echo "This script should be run with sudo for production deployment"
    echo "Usage: sudo $0 [up|down|logs|restart]"
    exit 1
fi

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed"
    exit 1
fi

# Determine which compose command to use
if command -v docker-compose &> /dev/null; then
    COMPOSE_CMD="docker-compose"
else
    COMPOSE_CMD="docker compose"
fi

# Create necessary directories with proper permissions
echo "Setting up directories..."
mkdir -p data
mkdir -p mosquitto/data
mkdir -p mosquitto/log
mkdir -p nginx/ssl

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating production .env file..."
    cat > .env <<EOF
MQTT_BROKER_HOST=mosquitto
MQTT_BROKER_PORT=1883
MQTT_TOPIC=msh/#
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
FLASK_DEBUG=False
DATABASE_PATH=/app/data/meshmonitor.db
EOF
    echo "Please edit .env file with your production configuration"
fi

# Parse command
COMMAND=${1:-up}

case $COMMAND in
    up)
        echo "Starting Meshtastic MQTT Monitor in production mode..."
        $COMPOSE_CMD -f docker-compose.prod.yml up -d
        echo ""
        echo "================================================"
        echo "Production deployment complete!"
        echo "================================================"
        echo "Services running:"
        $COMPOSE_CMD -f docker-compose.prod.yml ps
        echo ""
        echo "Next steps:"
        echo "1. Configure your domain DNS to point to this server"
        echo "2. Set up SSL certificates (see README.md)"
        echo "3. Update nginx/nginx.conf with your domain"
        echo "4. Configure MQTT authentication if needed"
        echo ""
        echo "Useful commands:"
        echo "  View logs: $COMPOSE_CMD -f docker-compose.prod.yml logs -f"
        echo "  Stop: $COMPOSE_CMD -f docker-compose.prod.yml down"
        echo "================================================"
        ;;
    down)
        echo "Stopping production deployment..."
        $COMPOSE_CMD -f docker-compose.prod.yml down
        ;;
    logs)
        $COMPOSE_CMD -f docker-compose.prod.yml logs -f
        ;;
    restart)
        echo "Restarting production deployment..."
        $COMPOSE_CMD -f docker-compose.prod.yml restart
        ;;
    ps)
        $COMPOSE_CMD -f docker-compose.prod.yml ps
        ;;
    *)
        echo "Usage: sudo $0 {up|down|logs|restart|ps}"
        exit 1
        ;;
esac
