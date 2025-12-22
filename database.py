"""Database management for Meshtastic messages"""
import sqlite3
import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional, TYPE_CHECKING
import config

if TYPE_CHECKING:
    from meshtastic_parser import MeshtasticMessage

class Database:
    def __init__(self, db_path: str = None):
        self.db_path = db_path or config.DATABASE_PATH
        # Ensure the directory exists
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
        self.init_db()

    def get_connection(self):
        """Get a database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        """Initialize the database schema"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Messages table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message_id TEXT,
                from_node TEXT NOT NULL,
                to_node TEXT,
                channel INTEGER,
                packet_type TEXT,
                payload TEXT,
                latitude REAL,
                longitude REAL,
                altitude REAL,
                snr REAL,
                rssi REAL,
                hop_limit INTEGER,
                hop_start INTEGER,
                received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                raw_data TEXT,
                UNIQUE(message_id, from_node, received_at)
            )
        ''')

        # Nodes table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS nodes (
                node_id TEXT PRIMARY KEY,
                long_name TEXT,
                short_name TEXT,
                hardware_model TEXT,
                last_seen TIMESTAMP,
                last_latitude REAL,
                last_longitude REAL,
                message_count INTEGER DEFAULT 0
            )
        ''')

        # Create indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_from_node ON messages(from_node)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_received_at ON messages(received_at DESC)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_latitude ON messages(latitude)')

        conn.commit()
        conn.close()

    def insert_message(self, message_data: "MeshtasticMessage") -> Optional[int]:
        """Insert a new message into the database"""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute('''
                INSERT INTO messages (
                    message_id, from_node, to_node, channel, packet_type,
                    payload, latitude, longitude, altitude, snr, rssi,
                    hop_limit
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                message_data.get('message_id'),
                message_data.get('from_node'),
                message_data.get('to_node'),
                message_data.get('channel'),
                message_data.get('packet_type'),
                message_data.get('payload'),
                message_data.get('latitude'),
                message_data.get('longitude'),
                message_data.get('altitude'),
                message_data.get('snr'),
                message_data.get('rssi'),
                message_data.get('hop_limit')
            ))

            message_id = cursor.lastrowid
            conn.commit()

            # Update node information
            self.update_node(message_data)

            return message_id
        except sqlite3.IntegrityError as e:
            # Duplicate message, ignore
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"IntegrityError inserting message: {e}")
            logger.warning(f"Message data: message_id={message_data.get('message_id')}, from_node={message_data.get('from_node')}, packet_type={message_data.get('packet_type')}")
            return -1
        finally:
            conn.close()

    def update_node(self, message_data: "MeshtasticMessage") -> None:
        """Update node information"""
        conn = self.get_connection()
        cursor = conn.cursor()

        from_node = message_data.get('from_node')
        if not from_node:
            conn.close()
            return

        cursor.execute('''
            INSERT INTO nodes (node_id, last_seen, message_count, last_latitude, last_longitude)
            VALUES (?, CURRENT_TIMESTAMP, 1, ?, ?)
            ON CONFLICT(node_id) DO UPDATE SET
                last_seen = CURRENT_TIMESTAMP,
                message_count = message_count + 1,
                last_latitude = COALESCE(?, last_latitude),
                last_longitude = COALESCE(?, last_longitude)
        ''', (
            from_node,
            message_data.get('latitude'),
            message_data.get('longitude'),
            message_data.get('latitude'),
            message_data.get('longitude')
        ))

        conn.commit()
        conn.close()

    def get_messages(self, limit: int = None, offset: int = 0, node_id: str = None) -> List[Dict[str, Any]]:
        """Get messages from the database"""
        conn = self.get_connection()
        cursor = conn.cursor()

        query = 'SELECT * FROM messages'
        params = []

        if node_id:
            query += ' WHERE from_node = ?'
            params.append(node_id)

        query += ' ORDER BY received_at DESC'

        if limit:
            query += ' LIMIT ? OFFSET ?'
            params.extend([limit, offset])

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def get_nodes(self) -> List[Dict[str, Any]]:
        """Get all nodes"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT * FROM nodes
            ORDER BY last_seen DESC
        ''')

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def get_messages_with_location(self) -> List[Dict[str, Any]]:
        """Get messages that have location data"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT * FROM messages
            WHERE latitude IS NOT NULL AND longitude IS NOT NULL
            ORDER BY received_at DESC
            LIMIT 500
        ''')

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT COUNT(*) as total FROM messages')
        total_messages = cursor.fetchone()['total']

        cursor.execute('SELECT COUNT(*) as total FROM nodes')
        total_nodes = cursor.fetchone()['total']

        cursor.execute('''
            SELECT COUNT(*) as total FROM messages
            WHERE latitude IS NOT NULL AND longitude IS NOT NULL
        ''')
        messages_with_location = cursor.fetchone()['total']

        conn.close()

        return {
            'total_messages': total_messages,
            'total_nodes': total_nodes,
            'messages_with_location': messages_with_location
        }
