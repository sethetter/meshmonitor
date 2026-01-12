"""Flask API server for Meshtastic Monitor"""
from typing import Optional
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import logging
from database import Database
import config

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='static', static_url_path='')
CORS(app)

# Initialize database
db = Database()

@app.route('/')
def index():
    """Serve the main HTML page"""
    return send_from_directory('static', 'index.html')

@app.route('/api/messages', methods=['GET'])
def get_messages():
    """Get messages with optional filtering"""
    try:
        limit = request.args.get('limit', 100, type=int)
        offset = request.args.get('offset', 0, type=int)
        node_id = request.args.get('node_id', None)

        messages = db.get_messages(limit=limit, offset=offset, node_id=node_id)

        return jsonify({
            'success': True,
            'messages': messages,
            'count': len(messages)
        })
    except Exception as e:
        logger.error(f"Error getting messages: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/nodes', methods=['GET'])
def get_nodes():
    """Get all nodes"""
    try:
        nodes = db.get_nodes()

        return jsonify({
            'success': True,
            'nodes': nodes,
            'count': len(nodes)
        })
    except Exception as e:
        logger.error(f"Error getting nodes: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/messages/locations', methods=['GET'])
def get_message_locations():
    """Get messages with location data for map display"""
    try:
        messages = db.get_messages_with_location()

        return jsonify({
            'success': True,
            'messages': messages,
            'count': len(messages)
        })
    except Exception as e:
        logger.error(f"Error getting message locations: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get database statistics"""
    try:
        stats = db.get_stats()

        return jsonify({
            'success': True,
            'stats': stats
        })
    except Exception as e:
        logger.error(f"Error getting stats: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'success': True,
        'status': 'healthy',
        'database': 'connected'
    })

@app.route('/api/ingest/meshlink', methods=['POST'])
def ingest_meshlink_data():
    """
    Ingest data from MeshLinkBeta plugin

    Accepts batch data with nodes, packets, topology, and traceroutes
    and stores them in MeshMonitor's database
    """
    try:
        # Get JSON data
        data = request.get_json()

        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400

        collector_id = data.get('collector_id')
        batch_data = data.get('data', {})

        if not collector_id:
            return jsonify({
                'success': False,
                'error': 'collector_id required'
            }), 400

        logger.info(f"Receiving batch from collector '{collector_id}'")

        results = {
            'nodes': {'accepted': 0, 'rejected': 0},
            'packets': {'accepted': 0, 'rejected': 0},
            'topology': {'accepted': 0, 'rejected': 0},
            'traceroutes': {'accepted': 0, 'rejected': 0}
        }

        # Process nodes
        if 'nodes' in batch_data:
            for node in batch_data['nodes']:
                try:
                    db.upsert_node_from_meshlink(node)
                    results['nodes']['accepted'] += 1
                except Exception as e:
                    logger.error(f"Error inserting node: {e}")
                    results['nodes']['rejected'] += 1

        # Process packets
        if 'packets' in batch_data:
            for packet in batch_data['packets']:
                try:
                    db.insert_packet_from_meshlink(packet, collector_id)
                    results['packets']['accepted'] += 1
                except Exception as e:
                    logger.error(f"Error inserting packet: {e}")
                    results['packets']['rejected'] += 1

        # Process topology (store as special messages for now)
        if 'topology' in batch_data:
            for link in batch_data['topology']:
                try:
                    db.insert_topology_link(link, collector_id)
                    results['topology']['accepted'] += 1
                except Exception as e:
                    logger.error(f"Error inserting topology: {e}")
                    results['topology']['rejected'] += 1

        # Process traceroutes (store as special messages)
        if 'traceroutes' in batch_data:
            for trace in batch_data['traceroutes']:
                try:
                    db.insert_traceroute(trace, collector_id)
                    results['traceroutes']['accepted'] += 1
                except Exception as e:
                    logger.error(f"Error inserting traceroute: {e}")
                    results['traceroutes']['rejected'] += 1

        total_accepted = sum(r['accepted'] for r in results.values())
        total_rejected = sum(r['rejected'] for r in results.values())

        logger.info(f"Batch processed: {total_accepted} accepted, {total_rejected} rejected")

        return jsonify({
            'success': True,
            'summary': {
                'total_items': total_accepted + total_rejected,
                'accepted': total_accepted,
                'rejected': total_rejected
            },
            'details': results
        })

    except Exception as e:
        logger.error(f"Error processing MeshLink batch: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def run_server(host: Optional[str] = None, port: Optional[int] = None, debug: Optional[bool] = None):
    """Run the Flask server"""
    host = host or config.FLASK_HOST
    port = port or config.FLASK_PORT
    debug = debug if debug is not None else config.FLASK_DEBUG

    logger.info(f"Starting Flask server on {host}:{port}")
    app.run(host=host, port=port, debug=debug, threaded=True)

if __name__ == '__main__':
    run_server()
