"""Parser for Meshtastic MQTT messages"""
import json
import logging
from typing import Dict, Any, Optional
import base64

logger = logging.getLogger(__name__)

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

    def parse_message(self, topic: str, payload: bytes) -> Optional[Dict[str, Any]]:
        """
        Parse a Meshtastic MQTT message

        Args:
            topic: MQTT topic (e.g., 'msh/US/2/e/LongFast/!abc123')
            payload: Message payload (typically JSON)

        Returns:
            Dictionary with parsed message data or None if parsing fails
        """
        try:
            # Parse topic
            topic_parts = topic.split('/')

            # Try to parse JSON payload
            try:
                data = json.loads(payload.decode('utf-8'))
            except (json.JSONDecodeError, UnicodeDecodeError):
                # Payload might be binary protobuf data
                logger.debug(f"Non-JSON payload on topic {topic}")
                return None

            # Extract message fields
            message = {
                'topic': topic,
                'from_node': self._extract_node_id(data.get('from')),
                'to_node': self._extract_node_id(data.get('to')),
                'channel': data.get('channel'),
                'message_id': str(data.get('id')),
                'packet_type': None,
                'payload': None,
                'latitude': None,
                'longitude': None,
                'altitude': None,
                'snr': data.get('snr'),
                'rssi': data.get('rssi'),
                'hop_limit': data.get('hopLimit'),
                'hop_start': data.get('hopStart'),
                'raw_data': data
            }

            # Parse the packet/payload based on type
            if 'decoded' in data:
                decoded = data['decoded']

                # Get packet type
                port_num = decoded.get('portnum')
                if port_num:
                    message['packet_type'] = port_num.replace('_', ' ').title()

                # Parse payload based on type
                if 'payload' in decoded:
                    payload_data = decoded['payload']

                    if isinstance(payload_data, str):
                        # Text message
                        try:
                            message['payload'] = base64.b64decode(payload_data).decode('utf-8')
                        except:
                            message['payload'] = payload_data
                    elif isinstance(payload_data, dict):
                        message['payload'] = json.dumps(payload_data)

                # Parse position data
                if 'position' in decoded:
                    pos = decoded['position']
                    message['latitude'] = pos.get('latitude') or pos.get('latitudeI', 0) / 1e7
                    message['longitude'] = pos.get('longitude') or pos.get('longitudeI', 0) / 1e7
                    message['altitude'] = pos.get('altitude')

                    # Ensure valid coordinates
                    if message['latitude'] == 0 and message['longitude'] == 0:
                        message['latitude'] = None
                        message['longitude'] = None

                # Parse text message
                if 'text' in decoded:
                    message['payload'] = decoded['text']
                    message['packet_type'] = 'Text Message'

                # Parse user info (nodeinfo)
                if 'user' in decoded:
                    user = decoded['user']
                    message['packet_type'] = 'Node Info'
                    message['payload'] = json.dumps({
                        'longName': user.get('longName'),
                        'shortName': user.get('shortName'),
                        'macaddr': user.get('macaddr'),
                        'hwModel': user.get('hwModel')
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
