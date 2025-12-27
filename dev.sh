#!/usr/bin/env bash
# Local development script - runs single container matching production
set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IMAGE_NAME="meshmonitor:dev"
CONTAINER_NAME="meshmonitor-dev"

cd "$PROJECT_DIR"

# Parse arguments
ACTION="${1:-run}"

case "$ACTION" in
	build)
		echo "Building image..."
		docker build -t "$IMAGE_NAME" .
		;;
	run)
		# Build if image doesn't exist
		if ! docker image inspect "$IMAGE_NAME" &>/dev/null; then
			echo "Image not found, building..."
			docker build -t "$IMAGE_NAME" .
		fi

		# Stop existing container if running
		if docker ps -q -f name="$CONTAINER_NAME" | grep -q .; then
			echo "Stopping existing container..."
			docker stop "$CONTAINER_NAME"
		fi
		if docker ps -aq -f name="$CONTAINER_NAME" | grep -q .; then
			docker rm "$CONTAINER_NAME"
		fi

		# Create data directory if needed
		mkdir -p "$PROJECT_DIR/data"

		echo "Starting container..."
		docker run -d \
			--name "$CONTAINER_NAME" \
			-p 5000:5000 \
			-p 1883:1883 \
			-p 8883:8883 \
			-v "$PROJECT_DIR/data:/data" \
			-e MQTT_BROKER_HOST=127.0.0.1 \
			-e MQTT_BROKER_PORT=1883 \
			-e DATABASE_PATH=/data/meshmonitor.db \
			-e FLASK_HOST=0.0.0.0 \
			-e FLASK_PORT=5000 \
			"$IMAGE_NAME"

		echo ""
		echo "Container started!"
		echo "  Web UI:  http://localhost:5000"
		echo "  MQTT:    localhost:1883"
		echo ""
		echo "View logs: docker logs -f $CONTAINER_NAME"
		;;
	stop)
		echo "Stopping container..."
		docker stop "$CONTAINER_NAME" 2>/dev/null || true
		docker rm "$CONTAINER_NAME" 2>/dev/null || true
		echo "Stopped."
		;;
	logs)
		docker logs -f "$CONTAINER_NAME"
		;;
	rebuild)
		echo "Rebuilding and restarting..."
		docker stop "$CONTAINER_NAME" 2>/dev/null || true
		docker rm "$CONTAINER_NAME" 2>/dev/null || true
		docker build -t "$IMAGE_NAME" .
		exec "$0" run
		;;
	*)
		echo "Usage: $0 {build|run|stop|logs|rebuild}"
		echo ""
		echo "Commands:"
		echo "  build   - Build the Docker image"
		echo "  run     - Run the container (builds if needed)"
		echo "  stop    - Stop and remove the container"
		echo "  logs    - Tail container logs"
		echo "  rebuild - Rebuild image and restart container"
		exit 1
		;;
esac
