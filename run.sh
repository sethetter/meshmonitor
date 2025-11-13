#!/bin/bash
# Simple script to run the Meshtastic MQTT Monitor

echo "Starting Meshtastic MQTT Monitor..."
echo "=================================="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install/update dependencies
echo "Installing dependencies..."
pip install -q -r requirements.txt

# Run the application
echo "Starting application..."
echo "Web interface: http://localhost:5000"
echo "Press Ctrl+C to stop"
echo "=================================="
python main.py
