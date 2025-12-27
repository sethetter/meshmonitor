#!/bin/bash
set -e

DB_PATH="${DATABASE_PATH:-/data/meshmonitor.db}"
DB_DIR=$(dirname "$DB_PATH")

# Ensure data directory exists
mkdir -p "$DB_DIR"

# Require MQTT auth password to be set
# if [ -z "$MQTT_AUTH_PASSWORD" ]; then
#     echo "Error: MQTT_AUTH_PASSWORD must be set"
#     exit 1
# fi
#
# # Generate mosquitto password file
# MQTT_USER="${MQTT_AUTH_USER:-meshtastic}"
# echo "Generating mosquitto password file for user: $MQTT_USER"
# mosquitto_passwd -b -c /mosquitto/config/passwd "$MQTT_USER" "$MQTT_AUTH_PASSWORD"

# Start mosquitto in the background
echo "Starting Mosquitto..."
/usr/sbin/mosquitto -c /mosquitto/config/mosquitto.conf &
MOSQUITTO_PID=$!

# Handle shutdown gracefully
cleanup() {
	echo "Shutting down..."
	kill $MOSQUITTO_PID 2>/dev/null || true
	wait $MOSQUITTO_PID 2>/dev/null || true
	exit 0
}
trap cleanup SIGTERM SIGINT

# Wait for mosquitto to be ready
wait_for_mosquitto() {
	local host="${MQTT_BROKER_HOST:-127.0.0.1}"
	local port="${MQTT_BROKER_PORT:-1883}"
	local max_attempts=30
	local attempt=1

	echo "Waiting for Mosquitto at ${host}:${port}..."
	while [ $attempt -le $max_attempts ]; do
		if python -c "import socket; s=socket.socket(); s.settimeout(1); s.connect(('${host}', ${port})); s.close()" 2>/dev/null; then
			echo "Mosquitto is ready"
			return 0
		fi
		echo "Attempt $attempt/$max_attempts: Mosquitto not ready, waiting..."
		sleep 1
		attempt=$((attempt + 1))
	done

	echo "Error: Could not connect to Mosquitto after $max_attempts attempts"
	return 1
}

# Restore database from Litestream replica if local copy does not exist
if [ -n "$BUCKET_NAME" ] && [ ! -f "$DB_PATH" ]; then
	echo "Restoring database from Litestream replica..."
	litestream restore -config /etc/litestream.yml -if-replica-exists "$DB_PATH"
fi

# Wait for mosquitto before starting app
wait_for_mosquitto

# Start with or without Litestream replication
if [ -n "$BUCKET_NAME" ]; then
	echo "Starting app with Litestream replication..."
	litestream replicate -config /etc/litestream.yml -exec "python app/main.py" &
	APP_PID=$!
else
	echo "Starting app without replication (BUCKET_NAME not set)"
	python app/main.py &
	APP_PID=$!
fi

# Wait for either process to exit
wait -n $MOSQUITTO_PID $APP_PID 2>/dev/null || wait $APP_PID

# If we get here, one process died - clean up and exit
cleanup
