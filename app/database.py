"""Database management for Meshtastic messages"""
import sqlite3
import json
import os
from typing import List, Dict, Any, Optional, TYPE_CHECKING
import config

if TYPE_CHECKING:
    from meshtastic_parser import MeshtasticMessage

class Database:
    def __init__(self, db_path: Optional[str] = None):
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
                mqtt_source_node TEXT,
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
                first_seen TIMESTAMP,
                last_seen TIMESTAMP,
                last_latitude REAL,
                last_longitude REAL,
                message_count INTEGER DEFAULT 0,
                battery_level INTEGER,
                voltage REAL,
                is_charging INTEGER DEFAULT 0,
                total_packets_received INTEGER DEFAULT 0
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
                    message_id, from_node, to_node, mqtt_source_node, channel,
                    packet_type, payload, latitude, longitude, altitude, snr, rssi,
                    hop_limit
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                message_data.get('message_id'),
                message_data.get('from_node'),
                message_data.get('to_node'),
                message_data.get('mqtt_source_node'),
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

        # Extract long_name and short_name from nodeinfo packets
        long_name = None
        short_name = None
        payload = message_data.get('payload')
        if message_data.get('packet_type') == 'NODEINFO_APP' and payload:
            try:
                payload_data = json.loads(payload)
                long_name = payload_data.get('longName')
                short_name = payload_data.get('shortName')
            except (json.JSONDecodeError, TypeError):
                pass

        cursor.execute('''
            INSERT INTO nodes (node_id, long_name, short_name, last_seen, message_count, last_latitude, last_longitude)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP, 1, ?, ?)
            ON CONFLICT(node_id) DO UPDATE SET
                last_seen = CURRENT_TIMESTAMP,
                message_count = message_count + 1,
                long_name = COALESCE(?, long_name),
                short_name = COALESCE(?, short_name),
                last_latitude = COALESCE(?, last_latitude),
                last_longitude = COALESCE(?, last_longitude)
        ''', (
            from_node,
            long_name,
            short_name,
            message_data.get('latitude'),
            message_data.get('longitude'),
            long_name,
            short_name,
            message_data.get('latitude'),
            message_data.get('longitude')
        ))

        conn.commit()
        conn.close()

    def get_messages(self, limit: Optional[int] = None, offset: int = 0, node_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get messages from the database"""
        conn = self.get_connection()
        cursor = conn.cursor()

        query = 'SELECT * FROM messages'
        params: List[Any] = []

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
            SELECT
                node_id,
                long_name,
                short_name,
                hardware_model,
                first_seen,
                last_seen as last_seen_utc,
                last_latitude as latitude,
                last_longitude as longitude,
                message_count,
                battery_level,
                voltage,
                is_charging,
                total_packets_received
            FROM nodes
            ORDER BY last_seen DESC
        ''')

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def get_node(self, node_id: str):
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT
                node_id,
                long_name,
                short_name,
                hardware_model,
                first_seen,
                last_seen as last_seen_utc,
                last_latitude as latitude,
                last_longitude as longitude,
                message_count,
                battery_level,
                voltage,
                is_charging,
                total_packets_received
            FROM nodes
            WHERE node_id = ?
        ''', (node_id,))

        row = cursor.fetchone()
        conn.close()

        return row

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

    def upsert_node_from_meshlink(self, node_data: Dict[str, Any]) -> None:
        """Insert or update node from MeshLinkBeta data"""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute('''
                INSERT INTO nodes (
                    node_id, long_name, short_name, hardware_model,
                    first_seen, last_seen, last_latitude, last_longitude, message_count,
                    battery_level, voltage, is_charging, total_packets_received
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(node_id) DO UPDATE SET
                    long_name = COALESCE(?, long_name),
                    short_name = COALESCE(?, short_name),
                    hardware_model = COALESCE(?, hardware_model),
                    first_seen = COALESCE(first_seen, ?),
                    last_seen = ?,
                    last_latitude = COALESCE(?, last_latitude),
                    last_longitude = COALESCE(?, last_longitude),
                    message_count = COALESCE(?, message_count),
                    battery_level = COALESCE(?, battery_level),
                    voltage = COALESCE(?, voltage),
                    is_charging = COALESCE(?, is_charging),
                    total_packets_received = COALESCE(?, total_packets_received)
            ''', (
                node_data.get('node_id'),
                node_data.get('long_name'),
                node_data.get('short_name'),
                node_data.get('hardware_model'),
                node_data.get('first_seen_utc'),
                node_data.get('last_seen_utc'),
                node_data.get('latitude'),
                node_data.get('longitude'),
                node_data.get('total_packets_received', 0),
                node_data.get('battery_level'),
                node_data.get('voltage'),
                node_data.get('is_charging', 0),
                node_data.get('total_packets_received', 0),
                # For UPDATE clause
                node_data.get('long_name'),
                node_data.get('short_name'),
                node_data.get('hardware_model'),
                node_data.get('first_seen_utc'),
                node_data.get('last_seen_utc'),
                node_data.get('latitude'),
                node_data.get('longitude'),
                node_data.get('total_packets_received'),
                node_data.get('battery_level'),
                node_data.get('voltage'),
                node_data.get('is_charging'),
                node_data.get('total_packets_received')
            ))
            conn.commit()
        finally:
            conn.close()

    def insert_packet_from_meshlink(self, packet_data: Dict[str, Any], collector_id: str) -> Optional[int]:
        """Insert packet from MeshLinkBeta data"""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            # Map MeshLink packet format to MeshMonitor message format
            cursor.execute('''
                INSERT INTO messages (
                    message_id, from_node, to_node, mqtt_source_node, channel,
                    packet_type, payload, latitude, longitude, altitude,
                    snr, rssi, hop_limit, hop_start, received_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                f"meshlink-{packet_data.get('received_at_utc', '')}-{packet_data.get('node_id', '')}",
                packet_data.get('node_id'),
                None,  # to_node not in MeshLink packet schema
                packet_data.get('relay_node_id'),
                packet_data.get('channel_index', 0),
                packet_data.get('packet_type'),
                None,  # payload/message text not included for privacy
                packet_data.get('latitude'),
                packet_data.get('longitude'),
                packet_data.get('altitude'),
                packet_data.get('rx_snr'),
                packet_data.get('rx_rssi'),
                packet_data.get('hop_limit'),
                packet_data.get('hop_start'),
                packet_data.get('received_at_utc')
            ))

            message_id = cursor.lastrowid
            conn.commit()
            return message_id
        except sqlite3.IntegrityError:
            # Duplicate, ignore
            return -1
        finally:
            conn.close()

    def insert_topology_link(self, link_data: Dict[str, Any], collector_id: str) -> Optional[int]:
        """Insert network topology link as a special message"""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            # Store topology as a special message type
            payload = json.dumps({
                'source': link_data.get('source_node_id'),
                'neighbor': link_data.get('neighbor_node_id'),
                'avg_snr': link_data.get('avg_snr'),
                'avg_rssi': link_data.get('avg_rssi'),
                'total_packets': link_data.get('total_packets'),
                'link_quality': link_data.get('link_quality_score')
            })

            cursor.execute('''
                INSERT INTO messages (
                    message_id, from_node, to_node, packet_type,
                    payload, snr, rssi, received_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                f"topo-{link_data.get('source_node_id')}-{link_data.get('neighbor_node_id')}-{link_data.get('last_heard_utc')}",
                link_data.get('source_node_id'),
                link_data.get('neighbor_node_id'),
                'TOPOLOGY_LINK',
                payload,
                link_data.get('avg_snr'),
                link_data.get('avg_rssi'),
                link_data.get('last_heard_utc')
            ))

            message_id = cursor.lastrowid
            conn.commit()
            return message_id
        except sqlite3.IntegrityError:
            return -1
        finally:
            conn.close()

    def insert_traceroute(self, trace_data: Dict[str, Any], collector_id: str) -> Optional[int]:
        """Insert traceroute as a special message"""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute('''
                INSERT INTO messages (
                    message_id, from_node, to_node, packet_type,
                    payload, received_at
                ) VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                f"trace-{trace_data.get('from_node_id')}-{trace_data.get('to_node_id')}-{trace_data.get('received_at_utc')}",
                trace_data.get('from_node_id'),
                trace_data.get('to_node_id'),
                'TRACEROUTE',
                trace_data.get('route_json'),
                trace_data.get('received_at_utc')
            ))

            message_id = cursor.lastrowid
            conn.commit()
            return message_id
        except sqlite3.IntegrityError:
            return -1
        finally:
            conn.close()

    def get_node_packets(self, node_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get packet history for a specific node"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT * FROM messages
            WHERE from_node = ?
            ORDER BY received_at DESC
            LIMIT ?
        ''', (node_id, limit))

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def get_node_neighbors(self, node_id: str) -> List[Dict[str, Any]]:
        """Get neighbors for a specific node from topology data"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Get topology links where this node is involved
        cursor.execute('''
            SELECT * FROM messages
            WHERE packet_type = 'TOPOLOGY_LINK'
            AND (from_node = ? OR to_node = ?)
            ORDER BY received_at DESC
        ''', (node_id, node_id))

        rows = cursor.fetchall()
        conn.close()

        neighbors = []
        for row in rows:
            try:
                payload = json.loads(row['payload']) if row['payload'] else {}
                neighbors.append({
                    'neighbor_node_id': row['to_node'] if row['from_node'] == node_id else row['from_node'],
                    'source_node_id': row['from_node'],
                    'link_quality_score': payload.get('link_quality'),
                    'avg_snr': payload.get('avg_snr'),
                    'avg_rssi': payload.get('avg_rssi'),
                    'total_packets': payload.get('total_packets'),
                    'last_heard_utc': row['received_at']
                })
            except (json.JSONDecodeError, TypeError):
                pass

        return neighbors

    def get_topology(self, active_only: bool = True) -> List[Dict[str, Any]]:
        """Get network topology links"""
        conn = self.get_connection()
        cursor = conn.cursor()

        query = '''
            SELECT * FROM messages
            WHERE packet_type = 'TOPOLOGY_LINK'
        '''

        if active_only:
            # Only include topology links from the last 24 hours
            query += " AND datetime(received_at) > datetime('now', '-24 hours')"

        query += " ORDER BY received_at DESC"

        cursor.execute(query)
        rows = cursor.fetchall()
        conn.close()

        topology = []
        for row in rows:
            try:
                payload = json.loads(row['payload']) if row['payload'] else {}
                topology.append({
                    'source_node_id': row['from_node'],
                    'neighbor_node_id': row['to_node'],
                    'link_quality_score': payload.get('link_quality'),
                    'avg_snr': payload.get('avg_snr'),
                    'avg_rssi': payload.get('avg_rssi'),
                    'total_packets': payload.get('total_packets'),
                    'last_heard_utc': row['received_at']
                })
            except (json.JSONDecodeError, TypeError):
                pass

        return topology

    def get_hop_topology(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get topology organized by hop distance"""
        # Get all nodes
        nodes = self.get_nodes()

        graph_nodes = []
        graph_edges = []

        # Add local node placeholder
        graph_nodes.append({
            'id': 'LOCAL_NODE',
            'label': 'MeshMonitor',
            'short_name': 'MeshMonitor',
            'long_name': 'MeshMonitor Server',
            'hops': -1,
            'battery': None
        })

        # Process each node
        for node in nodes:
            node_id = node['node_id']

            # Get recent packets to determine hop count
            packets = self.get_node_packets(node_id, limit=20)

            min_hops = 99  # Default to unknown
            relay_via = None

            for pkt in packets:
                # Try to extract hop information from packet
                hop_limit = pkt.get('hop_limit')
                hop_start = pkt.get('hop_start')
                if hop_limit is not None and hop_start is not None:
                    hops = hop_start - hop_limit
                    if min_hops is None or hops < min_hops:
                        min_hops = hops

                    # Check if relayed
                    if hops > 0 and relay_via is None:
                        relay_via = pkt.get('mqtt_source_node')

            # Add node to graph
            graph_nodes.append({
                'id': node_id,
                'label': node.get('long_name') or node.get('short_name') or node_id,
                'short_name': node.get('short_name'),
                'long_name': node.get('long_name'),
                'hops': min_hops,
                'battery': None  # Not available in current schema
            })

            # Create edges based on hop count
            if min_hops == 0:
                graph_edges.append({
                    'from': 'LOCAL_NODE',
                    'to': node_id,
                    'hops': 0
                })
            elif relay_via and min_hops > 0:
                if isinstance(relay_via, str) and relay_via.startswith('!'):
                    graph_edges.append({
                        'from': relay_via,
                        'to': node_id,
                        'hops': min_hops
                    })

        return {
            'nodes': graph_nodes,
            'edges': graph_edges
        }

    def get_traceroutes(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get all traceroutes"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT * FROM messages
            WHERE packet_type = 'TRACEROUTE'
            ORDER BY received_at DESC
            LIMIT ?
        ''', (limit,))

        rows = cursor.fetchall()
        conn.close()

        traceroutes = []
        for row in rows:
            try:
                route_data = json.loads(row['payload']) if row['payload'] else []
                traceroutes.append({
                    'id': row['id'],
                    'from_node_id': row['from_node'],
                    'to_node_id': row['to_node'],
                    'route_json': row['payload'],
                    'route': route_data,
                    'hops': len(route_data) if isinstance(route_data, list) else 0,
                    'received_at_utc': row['received_at']
                })
            except (json.JSONDecodeError, TypeError):
                pass

        return traceroutes
