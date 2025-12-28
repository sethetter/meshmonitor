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
from api_server import run_server
from discord_notifier import post_to_discord
import config
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from meshtastic_parser import MeshtasticMessage

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MeshtasticMonitor:
    def __init__(self):
        self.db = Database()
        self.mqtt_broker = MQTTBroker(message_callback=self.on_message_received)
        self.running = False

    def on_message_received(self, message_data: "MeshtasticMessage") -> None:
        """Callback when a message is received from MQTT"""
        try:
            # Store message in database
            message_id = self.db.insert_message(message_data)

            if message_id and message_id > 0:
                logger.info(f"Stored message {message_id} from node {message_data.get('from_node')}")

                # Send text messages to Discord
                if message_data.get('packet_type') == 'TEXT_MESSAGE_APP':

                    mqtt_source_node_id = message_data.get('mqtt_source_node')
                    from_node_id = message_data.get('from_node')
                    to_node_id = message_data.get('to_node')

                    if not from_node_id or not to_node_id or not mqtt_source_node_id:
                        logger.error("Couldn't post to discord, no from/to node IDs")
                    else:
                        mqtt_source_node = self.db.get_node(mqtt_source_node_id)
                        from_node = self.db.get_node(from_node_id)
                        to_node = self.db.get_node(to_node_id)
                        num_hops = message_data.get('hop_limit') - message_data.get('hop_start')

                        post_to_discord(
                            mqtt_source_node["short_name"] if mqtt_source_node else mqtt_source_node_id,
                            from_node["short_name"] if from_node else from_node_id,
                            to_node["short_name"] if to_node else to_node_id,
                            num_hops,
                            message_data.get('payload') or '[missing message data]',
                        )
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
