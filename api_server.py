"""Flask API server for Meshtastic Monitor"""
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import logging
import os
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

def run_server(host: str = None, port: int = None, debug: bool = None):
    """Run the Flask server"""
    host = host or config.FLASK_HOST
    port = port or config.FLASK_PORT
    debug = debug if debug is not None else config.FLASK_DEBUG

    logger.info(f"Starting Flask server on {host}:{port}")
    app.run(host=host, port=port, debug=debug, threaded=True)

if __name__ == '__main__':
    run_server()
