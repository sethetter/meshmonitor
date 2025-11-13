#!/usr/bin/env python3
"""
Meshtastic MQTT Monitor - Main Application
Receives Meshtastic traffic via MQTT and displays messages with a web interface
"""
import logging
import signal
import sys
import threading
import time
from database import Database
from mqtt_broker import MQTTBroker
from api_server import run_server, db as api_db
import config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MeshtasticMonitor:
    def __init__(self):
        self.db = Database()
        self.mqtt_broker = MQTTBroker(message_callback=self.on_message_received)
        self.running = False

    def on_message_received(self, message_data):
        """Callback when a message is received from MQTT"""
        try:
            # Store message in database
            message_id = self.db.insert_message(message_data)

            if message_id > 0:
                logger.info(f"Stored message {message_id} from node {message_data.get('from_node')}")
            else:
                logger.debug("Duplicate message, skipped")

        except Exception as e:
            logger.error(f"Error storing message: {e}", exc_info=True)

    def start(self):
        """Start the monitor"""
        logger.info("=" * 60)
        logger.info("Starting Meshtastic MQTT Monitor")
        logger.info("=" * 60)
        logger.info(f"MQTT Broker: {config.MQTT_BROKER_HOST}:{config.MQTT_BROKER_PORT}")
        logger.info(f"Web Interface: http://{config.FLASK_HOST}:{config.FLASK_PORT}")
        logger.info(f"Database: {config.DATABASE_PATH}")
        logger.info("=" * 60)

        self.running = True

        # Start MQTT broker
        try:
            self.mqtt_broker.start()
            logger.info("MQTT client started successfully")
        except Exception as e:
            logger.error(f"Failed to start MQTT client: {e}")
            sys.exit(1)

        # Start Flask API server in a separate thread
        api_thread = threading.Thread(target=run_server, daemon=True)
        api_thread.start()
        logger.info("API server started successfully")

        # Keep running
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt")
            self.stop()

    def stop(self):
        """Stop the monitor"""
        logger.info("Stopping Meshtastic MQTT Monitor")
        self.running = False
        self.mqtt_broker.stop()
        logger.info("Shutdown complete")

def signal_handler(sig, frame):
    """Handle termination signals"""
    logger.info("Received termination signal")
    sys.exit(0)

if __name__ == '__main__':
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Create and start monitor
    monitor = MeshtasticMonitor()
    monitor.start()
