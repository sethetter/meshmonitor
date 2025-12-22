"""MQTT Broker for receiving Meshtastic messages"""
import paho.mqtt.client as mqtt
import logging
from typing import Callable, Optional, TYPE_CHECKING
import config
from meshtastic_parser import MeshtasticParser

if TYPE_CHECKING:
    from meshtastic_parser import MeshtasticMessage

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MQTTBroker:
    def __init__(self, message_callback: Optional[Callable[["MeshtasticMessage"], None]] = None):
        self.client = mqtt.Client()
        self.message_callback = message_callback
        self.parser = MeshtasticParser()

        # Set up callbacks
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect

    def on_connect(self, client, userdata, flags, rc):
        """Callback for when the client connects to the broker"""
        if rc == 0:
            logger.info(f"Connected to MQTT broker successfully")
            # Subscribe to Meshtastic topics
            client.subscribe(config.MQTT_TOPIC)
            logger.info(f"Subscribed to topic: {config.MQTT_TOPIC}")
        else:
            logger.error(f"Failed to connect to MQTT broker, return code {rc}")

    def on_disconnect(self, client, userdata, rc):
        """Callback for when the client disconnects"""
        if rc != 0:
            logger.warning(f"Unexpected disconnection from MQTT broker (code: {rc})")
        else:
            logger.info("Disconnected from MQTT broker")

    def on_message(self, client, userdata, msg):
        """Callback for when a message is received"""
        try:
            logger.info(f"Received message on topic: {msg.topic}")

            # Parse the Meshtastic message
            parsed_message = self.parser.parse_message(msg.topic, msg.payload)

            if parsed_message:
                logger.info(f"Parsed message from node: {parsed_message.get('from_node')}")

                # Call the callback if provided
                if self.message_callback:
                    self.message_callback(parsed_message)
            else:
                logger.debug(f"Could not parse message from topic: {msg.topic}")

        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)

    def start(self, host: Optional[str] = None, port: Optional[int] = None):
        """Start the MQTT client and connect to broker"""
        host = host or config.MQTT_BROKER_HOST
        port = port or config.MQTT_BROKER_PORT

        try:
            logger.info(f"Connecting to MQTT broker at {host}:{port}")
            self.client.connect(host, port, 60)
            self.client.loop_start()
        except Exception as e:
            logger.error(f"Failed to start MQTT client: {e}")
            raise

    def stop(self):
        """Stop the MQTT client"""
        logger.info("Stopping MQTT client")
        self.client.loop_stop()
        self.client.disconnect()
