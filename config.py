"""Configuration for Meshtastic MQTT Monitor"""
import os

# MQTT Configuration
MQTT_BROKER_HOST = os.getenv('MQTT_BROKER_HOST', '0.0.0.0')
MQTT_BROKER_PORT = int(os.getenv('MQTT_BROKER_PORT', 1883))
MQTT_TOPIC = os.getenv('MQTT_TOPIC', 'msh/#')  # Subscribe to all Meshtastic topics

# Flask Configuration
FLASK_HOST = os.getenv('FLASK_HOST', '0.0.0.0')
FLASK_PORT = int(os.getenv('FLASK_PORT', 5000))
FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'

# Database Configuration
DATABASE_PATH = os.getenv('DATABASE_PATH', 'meshmonitor.db')

# Application Configuration
MAX_MESSAGES_DISPLAYED = int(os.getenv('MAX_MESSAGES_DISPLAYED', 1000))
