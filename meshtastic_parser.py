"""Parser for Meshtastic MQTT messages"""
import json
import logging
from typing import Any, Optional, TypedDict
import base64
import meshtastic.mesh_pb2
import meshtastic.mqtt_pb2
from meshtastic.portnums_pb2 import NODEINFO_APP, POSITION_APP, TEXT_MESSAGE_APP

logger = logging.getLogger(__name__)


class MeshtasticMessage(TypedDict):
    """Type definition for parsed Meshtastic messages.

    Contains all fields extracted from a Meshtastic MQTT message.
    Note: raw_data field is intentionally excluded to avoid serialization issues.
    """
    topic: str
    from_node: Optional[str]
    to_node: Optional[str]
    channel: int
    message_id: str
    packet_type: Optional[str]
    payload: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]
    altitude: Optional[int]
    snr: float
    rssi: int
    hop_limit: int
    hop_start: int


class MeshtasticParser:
    """Parse Meshtastic MQTT messages into a structured format"""

    def __init__(self):
        self.packet_types = {
            'TEXT_MESSAGE_APP': 'text',
            'POSITION_APP': 'position',
            'NODEINFO_APP': 'nodeinfo',
            'TELEMETRY_APP': 'telemetry',
            'ROUTING_APP': 'routing',
            'ADMIN_APP': 'admin',
            'WAYPOINT_APP': 'waypoint',
            'NEIGHBORINFO_APP': 'neighborinfo'
        }

    def parse_message(self, topic: str, payload: bytes) -> Optional[MeshtasticMessage]:
        """
        Parse a Meshtastic MQTT message

        Args:
            topic: MQTT topic (e.g., 'msh/US/2/e/LongFast/!abc123')
            payload: Message payload (typically JSON)

        Returns:
            Dictionary with parsed message data or None if parsing fails
        """
        try:
            # First, try to parse as ServiceEnvelope (MQTT messages are wrapped)
            try:
                envelope = meshtastic.mqtt_pb2.ServiceEnvelope()
                envelope.ParseFromString(payload)
                data = envelope.packet
                logger.info(f"Parsed as ServiceEnvelope")
            except Exception as e:
                logger.warning(f"Failed to parse as ServiceEnvelope, trying as raw MeshPacket: {e}")
                # Fallback: try parsing as raw MeshPacket
                data = meshtastic.mesh_pb2.MeshPacket()
                data.ParseFromString(payload)
                logger.info(f"Parsed as raw MeshPacket")

            # Extract message fields (protobuf)
            message: MeshtasticMessage = {
                'topic': topic,
                'from_node': self._extract_node_id(getattr(data, 'from', None)),
                'to_node': self._extract_node_id(data.to),
                'channel': data.channel,
                'message_id': str(data.id),
                'packet_type': None,
                'payload': None,
                'latitude': None,
                'longitude': None,
                'altitude': None,
                'snr': data.rx_snr,
                'rssi': data.rx_rssi,
                'hop_limit': data.hop_limit,
                'hop_start': data.hop_start,
            }

            logger.info(f"Message: {message}")

            # Parse the packet/payload based on type
            if data.HasField('decoded'):
                decoded = data.decoded

                # Get packet type
                port_num = decoded.portnum
                logger.debug(f"port_num value = {port_num}, type = {type(port_num)}")
                if port_num:
                    message['packet_type'] = str(port_num)

                # Parse payload based on type
                if decoded.payload:
                    payload_data = decoded.payload

                    if isinstance(payload_data, str):
                        # Text message
                        try:
                            message['payload'] = base64.b64decode(payload_data).decode('utf-8')
                        except:
                            message['payload'] = payload_data
                    elif isinstance(payload_data, dict):
                        message['payload'] = json.dumps(payload_data)

                # Parse position data
                if decoded.portnum == POSITION_APP:
                    pos = meshtastic.mesh_pb2.Position.FromString(decoded.payload)
                    message['latitude'] = pos.latitude_i / 1e7
                    message['longitude'] = pos.longitude_i / 1e7
                    message['altitude'] = pos.altitude

                    # Ensure valid coordinates
                    if message['latitude'] == 0 and message['longitude'] == 0:
                        message['latitude'] = None
                        message['longitude'] = None

                # Parse text message
                if decoded.portnum == TEXT_MESSAGE_APP:
                    message['payload'] = decoded.payload.decode('utf-8')
                    message['packet_type'] = 'Text Message'

                # Parse user info (nodeinfo)
                if decoded.portnum == NODEINFO_APP:
                    user = meshtastic.mesh_pb2.User.FromString(decoded.payload)
                    message['packet_type'] = 'Node Info'
                    message['payload'] = json.dumps({
                        'longName': user.long_name,
                        'shortName': user.short_name,
                        'macaddr': user.macaddr,
                        'hwModel': user.hw_model
                    })

            return message

        except Exception as e:
            logger.error(f"Error parsing message from topic {topic}: {e}", exc_info=True)
            return None


    def _extract_node_id(self, node_value: Any) -> Optional[str]:
        """Extract node ID from various formats"""
        if not node_value:
            return None

        if isinstance(node_value, str):
            return node_value
        elif isinstance(node_value, int):
            # Convert integer to hex format (e.g., !abc123)
            return f"!{node_value:08x}"

        return str(node_value)
