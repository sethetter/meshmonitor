"""Unit tests for database layer."""
import unittest
import tempfile
import os
import json
import sqlite3
from database import Database


def make_message(
    from_node="!abc123",
    to_node="!def456",
    channel=0,
    message_id="12345",
    packet_type="TEXT_MESSAGE_APP",
    payload="Test message",
    latitude=None,
    longitude=None,
    altitude=None,
    snr=5.5,
    rssi=-100,
    hop_limit=3,
    hop_start=3,
):
    """Helper to create a message dict for testing."""
    return {
        "topic": f"msh/US/2/e/LongFast/{from_node}",
        "from_node": from_node,
        "to_node": to_node,
        "channel": channel,
        "message_id": message_id,
        "packet_type": packet_type,
        "payload": payload,
        "latitude": latitude,
        "longitude": longitude,
        "altitude": altitude,
        "snr": snr,
        "rssi": rssi,
        "hop_limit": hop_limit,
        "hop_start": hop_start,
    }


class TestDatabaseInit(unittest.TestCase):
    """Test database initialization."""

    def test_creates_parent_directories(self):
        """Test that database creates parent directories if they don't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            nested_path = os.path.join(tmpdir, "nested", "dir", "test.db")
            Database(db_path=nested_path)
            self.assertTrue(os.path.exists(nested_path))

    def test_creates_database_file(self):
        """Test that database file is created."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as f:
            db_path = f.name
        try:
            # File exists but is empty from tempfile
            Database(db_path=db_path)
            self.assertTrue(os.path.exists(db_path))
            self.assertGreater(os.path.getsize(db_path), 0)
        finally:
            os.unlink(db_path)

    def test_creates_messages_table(self):
        """Test that messages table is created with correct schema."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as f:
            db_path = f.name
        try:
            Database(db_path=db_path)
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='messages'"
            )
            self.assertIsNotNone(cursor.fetchone())
            conn.close()
        finally:
            os.unlink(db_path)

    def test_creates_nodes_table(self):
        """Test that nodes table is created."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as f:
            db_path = f.name
        try:
            Database(db_path=db_path)
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='nodes'"
            )
            self.assertIsNotNone(cursor.fetchone())
            conn.close()
        finally:
            os.unlink(db_path)

    def test_creates_indexes(self):
        """Test that indexes are created."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as f:
            db_path = f.name
        try:
            Database(db_path=db_path)
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
            indexes = {row[0] for row in cursor.fetchall()}
            self.assertIn("idx_from_node", indexes)
            self.assertIn("idx_received_at", indexes)
            self.assertIn("idx_latitude", indexes)
            conn.close()
        finally:
            os.unlink(db_path)


class TestDatabaseInsertUpdate(unittest.TestCase):
    """Test message insertion and node updates."""

    def setUp(self):
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        self.temp_db.close()
        self.db = Database(db_path=self.temp_db.name)

    def tearDown(self):
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)

    def test_insert_message_returns_positive_id(self):
        """Test that insert_message returns a positive ID on success."""
        message = make_message()
        result = self.db.insert_message(message)
        self.assertGreater(result, 0)

    def test_insert_message_duplicate_returns_negative_one(self):
        """Test that inserting duplicate message returns -1."""
        message = make_message()
        first_result = self.db.insert_message(message)
        self.assertGreater(first_result, 0)

        # Insert same message again
        second_result = self.db.insert_message(message)
        self.assertEqual(second_result, -1)

    def test_insert_message_stores_all_fields(self):
        """Test that all message fields are stored correctly."""
        message = make_message(
            from_node="!test1",
            to_node="!test2",
            channel=5,
            message_id="unique123",
            packet_type="POSITION_APP",
            payload="test payload",
            latitude=37.7749,
            longitude=-122.4194,
            altitude=100.5,
            snr=8.5,
            rssi=-85,
            hop_limit=4,
        )
        self.db.insert_message(message)

        messages = self.db.get_messages()
        self.assertEqual(len(messages), 1)
        msg = messages[0]
        self.assertEqual(msg["from_node"], "!test1")
        self.assertEqual(msg["to_node"], "!test2")
        self.assertEqual(msg["channel"], 5)
        self.assertEqual(msg["packet_type"], "Position")
        self.assertEqual(msg["payload"], "test payload")
        self.assertAlmostEqual(msg["latitude"], 37.7749)
        self.assertAlmostEqual(msg["longitude"], -122.4194)
        self.assertAlmostEqual(msg["altitude"], 100.5)
        self.assertAlmostEqual(msg["snr"], 8.5)
        self.assertEqual(msg["rssi"], -85)
        self.assertEqual(msg["hop_limit"], 4)

    def test_update_node_creates_new_node(self):
        """Test that update_node creates a new node entry."""
        message = make_message(from_node="!newnode")
        self.db.insert_message(message)

        nodes = self.db.get_nodes()
        self.assertEqual(len(nodes), 1)
        self.assertEqual(nodes[0]["node_id"], "!newnode")

    def test_update_node_increments_message_count(self):
        """Test that message_count is incremented for each message."""
        for i in range(3):
            message = make_message(from_node="!counter", message_id=f"msg{i}")
            self.db.insert_message(message)

        nodes = self.db.get_nodes()
        self.assertEqual(len(nodes), 1)
        self.assertEqual(nodes[0]["message_count"], 3)

    def test_update_node_extracts_nodeinfo_names(self):
        """Test that long_name and short_name are extracted from Node Info packets."""
        payload = json.dumps({"longName": "Test Node", "shortName": "TN"})
        message = make_message(
            from_node="!nodeinfo",
            message_id="nodeinfo1",
            packet_type="NODEINFO_APP",
            payload=payload,
        )
        self.db.insert_message(message)

        nodes = self.db.get_nodes()
        self.assertEqual(len(nodes), 1)
        self.assertEqual(nodes[0]["long_name"], "Test Node")
        self.assertEqual(nodes[0]["short_name"], "TN")

    def test_update_node_updates_location(self):
        """Test that node location is updated from messages."""
        message = make_message(
            from_node="!located",
            message_id="loc1",
            latitude=40.7128,
            longitude=-74.0060,
        )
        self.db.insert_message(message)

        nodes = self.db.get_nodes()
        self.assertEqual(len(nodes), 1)
        self.assertAlmostEqual(nodes[0]["last_latitude"], 40.7128)
        self.assertAlmostEqual(nodes[0]["last_longitude"], -74.0060)

    def test_update_node_ignores_missing_from_node(self):
        """Test that update_node handles messages without from_node."""
        message = make_message(from_node=None)
        # Should not raise an error
        self.db.update_node(message)
        nodes = self.db.get_nodes()
        self.assertEqual(len(nodes), 0)


class TestDatabaseQueries(unittest.TestCase):
    """Test database query methods."""

    def setUp(self):
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        self.temp_db.close()
        self.db = Database(db_path=self.temp_db.name)

        # Insert some test data
        for i in range(5):
            self.db.insert_message(
                make_message(
                    from_node=f"!node{i % 2}",  # Alternates between !node0 and !node1
                    message_id=f"msg{i}",
                    latitude=37.0 + i if i % 2 == 0 else None,  # Only even messages have location
                    longitude=-122.0 + i if i % 2 == 0 else None,
                )
            )

    def tearDown(self):
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)

    def test_get_messages_returns_all(self):
        """Test that get_messages returns all messages."""
        messages = self.db.get_messages()
        self.assertEqual(len(messages), 5)

    def test_get_messages_with_limit(self):
        """Test that get_messages respects limit parameter."""
        messages = self.db.get_messages(limit=2)
        self.assertEqual(len(messages), 2)

    def test_get_messages_with_offset(self):
        """Test that get_messages respects offset parameter."""
        all_messages = self.db.get_messages()
        offset_messages = self.db.get_messages(limit=2, offset=2)
        self.assertEqual(len(offset_messages), 2)
        # Messages are ordered by received_at DESC
        self.assertEqual(offset_messages[0]["message_id"], all_messages[2]["message_id"])

    def test_get_messages_with_node_filter(self):
        """Test that get_messages filters by node_id."""
        messages = self.db.get_messages(node_id="!node0")
        self.assertEqual(len(messages), 3)  # Messages 0, 2, 4 are from node0
        for msg in messages:
            self.assertEqual(msg["from_node"], "!node0")

    def test_get_nodes_returns_all(self):
        """Test that get_nodes returns all unique nodes."""
        nodes = self.db.get_nodes()
        self.assertEqual(len(nodes), 2)
        node_ids = {n["node_id"] for n in nodes}
        self.assertEqual(node_ids, {"!node0", "!node1"})

    def test_get_nodes_ordered_by_last_seen(self):
        """Test that nodes are ordered by last_seen DESC."""
        nodes = self.db.get_nodes()
        # Last message was from !node0 (message 4), so it should be first
        self.assertEqual(nodes[0]["node_id"], "!node0")

    def test_get_messages_with_location(self):
        """Test that get_messages_with_location filters correctly."""
        messages = self.db.get_messages_with_location()
        self.assertEqual(len(messages), 3)  # Messages 0, 2, 4 have location
        for msg in messages:
            self.assertIsNotNone(msg["latitude"])
            self.assertIsNotNone(msg["longitude"])

    def test_get_stats(self):
        """Test that get_stats returns correct counts."""
        stats = self.db.get_stats()
        self.assertEqual(stats["total_messages"], 5)
        self.assertEqual(stats["total_nodes"], 2)
        self.assertEqual(stats["messages_with_location"], 3)


if __name__ == "__main__":
    unittest.main()
