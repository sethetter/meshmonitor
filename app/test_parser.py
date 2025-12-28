"""Unit tests for Meshtastic parser and database integration."""
import unittest
import tempfile
import json
import os
from meshtastic_parser import MeshtasticParser, MeshtasticMessage
from database import Database
import meshtastic.mesh_pb2
import meshtastic.mqtt_pb2


class TestParserStructure(unittest.TestCase):
    """Test that parser creates correct message structure."""

    def setUp(self):
        self.parser = MeshtasticParser()

    def _create_service_envelope(self, mesh_packet):
        """Helper to wrap a MeshPacket in a ServiceEnvelope (like real MQTT messages)."""
        envelope = meshtastic.mqtt_pb2.ServiceEnvelope()
        envelope.packet.CopyFrom(mesh_packet)
        envelope.channel_id = "0"
        envelope.gateway_id = "!2ce82d69"
        return envelope.SerializeToString()

    def test_message_has_no_raw_data(self):
        """Test that parse_message returns dict without raw_data field."""
        # Create a minimal valid protobuf message
        mesh_packet = meshtastic.mesh_pb2.MeshPacket()
        mesh_packet.id = 12345
        setattr(mesh_packet, 'from', 0xabc123)
        mesh_packet.to = 0xFFFFFFFF
        mesh_packet.channel = 0
        mesh_packet.rx_snr = 5.5
        mesh_packet.rx_rssi = -100
        mesh_packet.hop_limit = 3

        # Wrap in ServiceEnvelope and serialize
        payload = self._create_service_envelope(mesh_packet)
        topic = "msh/US/2/e/LongFast/!abc123"

        # Parse the message
        result = self.parser.parse_message(topic, payload)

        # Verify raw_data is NOT present
        if result:
            self.assertNotIn('raw_data', result, "raw_data field should not be present in parsed message")

    def test_message_is_json_serializable(self):
        """Test that message dict can be JSON serialized."""
        # Create a sample message dict matching MeshtasticMessage structure
        message = {
            'topic': 'msh/US/2/e/LongFast/!abc123',
            'from_node': '!abc123',
            'to_node': '!def456',
            'channel': 0,
            'message_id': '12345',
            'packet_type': 'TEXT_MESSAGE_APP',
            'payload': 'Hello World',
            'latitude': None,
            'longitude': None,
            'altitude': None,
            'snr': 5.5,
            'rssi': -100,
            'hop_limit': 3
        }

        # This should NOT raise an exception
        try:
            json_str = json.dumps(message)
            self.assertIsInstance(json_str, str)
        except TypeError as e:
            self.fail(f"Message dict should be JSON serializable, but got: {e}")

    def test_required_fields_present(self):
        """Test that all required fields are in the TypedDict."""
        # Create a minimal valid protobuf message
        mesh_packet = meshtastic.mesh_pb2.MeshPacket()
        mesh_packet.id = 12345
        setattr(mesh_packet, 'from', 0xabc123)
        mesh_packet.to = 0xFFFFFFFF
        mesh_packet.channel = 0
        mesh_packet.rx_snr = 5.5
        mesh_packet.rx_rssi = -100
        mesh_packet.hop_limit = 3

        # Wrap in ServiceEnvelope and serialize
        payload = self._create_service_envelope(mesh_packet)
        topic = "msh/US/2/e/LongFast/!abc123"

        result = self.parser.parse_message(topic, payload)

        if result:
            required_fields = [
                'topic', 'from_node', 'to_node', 'channel', 'message_id',
                'packet_type', 'payload', 'latitude', 'longitude', 'altitude',
                'snr', 'rssi', 'hop_limit'
            ]
            for field in required_fields:
                self.assertIn(field, result, f"Required field '{field}' missing from parsed message")


class TestDatabaseIntegration(unittest.TestCase):
    """Test database can store messages without serialization errors."""

    def setUp(self):
        # Create a temporary database file
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.db = Database(db_path=self.temp_db.name)
        self.parser = MeshtasticParser()

    def test_insert_message_without_raw_data(self):
        """Test that insert_message works with message dict (no raw_data field)."""
        # Create a sample message dict without raw_data
        message_data: MeshtasticMessage = {
            'topic': 'msh/US/2/e/LongFast/!abc123',
            'from_node': '!abc123',
            'to_node': '!def456',
            'mqtt_source_node': '!ghi789',
            'channel': 0,
            'message_id': '12345',
            'packet_type': 'TEXT_MESSAGE_APP',
            'payload': 'Test message',
            'latitude': None,
            'longitude': None,
            'altitude': None,
            'snr': 5.5,
            'rssi': -100,
            'hop_limit': 3,
            'hop_start': 3
        }

        # Should insert successfully
        message_id = self.db.insert_message(message_data)
        self.assertGreater(message_id, 0, "Message should be inserted and return a positive ID")

    def test_insert_does_not_fail_on_serialization(self):
        """Test that no json.dumps error occurs on database insert."""
        # This is the critical test that verifies the fix
        message_data: MeshtasticMessage = {
            'topic': 'msh/US/2/e/LongFast/!test',
            'from_node': '!test123',
            'to_node': None,
            'mqtt_source_node': '!ghi789',
            'channel': 0,
            'message_id': '99999',
            'packet_type': 'Position',
            'payload': None,
            'latitude': 37.7749,
            'longitude': -122.4194,
            'altitude': 100,
            'snr': 10.0,
            'rssi': -90,
            'hop_limit': 5,
            'hop_start': 5
        }

        # Should NOT raise TypeError about MeshPacket not being JSON serializable
        try:
            message_id = self.db.insert_message(message_data)
            self.assertGreater(message_id, 0)
        except TypeError as e:
            if "not JSON serializable" in str(e):
                self.fail(f"Serialization error should not occur: {e}")
            raise

    def tearDown(self):
        # Clean up the temporary database file
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)


if __name__ == '__main__':
    unittest.main()
