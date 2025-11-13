# Meshtastic MQTT Monitor

A real-time monitoring application for Meshtastic network traffic via MQTT. This application receives Meshtastic messages, stores them in a SQLite database, and displays them in a web interface with an interactive map.

## Features

- **MQTT Server Integration**: Connects to an MQTT broker to receive Meshtastic traffic
- **Message Storage**: Stores all messages in a SQLite database with full history
- **Real-time Web Interface**: View messages and nodes in real-time
- **Interactive Map**: Visualize message locations using Leaflet maps
- **Node Tracking**: Track all nodes that have sent messages
- **Message Filtering**: Filter messages by node
- **Statistics Dashboard**: View total messages, active nodes, and location data

## Technology Stack

- **Backend**: Python 3 with Paho MQTT
- **Frontend**: Plain HTML/JavaScript (no build process required)
- **Map**: Leaflet (open-source, no API key needed)
- **Database**: SQLite (file-based, simple)
- **Web Framework**: Flask for REST API

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Access to an MQTT broker (e.g., Mosquitto)

### Setup

1. Clone or navigate to the repository:
```bash
cd meshmonitor
```

2. Create a virtual environment (recommended):
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Configuration

The application can be configured using environment variables or by editing `config.py`:

### Environment Variables

- `MQTT_BROKER_HOST`: MQTT broker hostname (default: `0.0.0.0`)
- `MQTT_BROKER_PORT`: MQTT broker port (default: `1883`)
- `MQTT_TOPIC`: MQTT topic to subscribe to (default: `msh/#`)
- `FLASK_HOST`: Web server host (default: `0.0.0.0`)
- `FLASK_PORT`: Web server port (default: `5000`)
- `DATABASE_PATH`: Path to SQLite database file (default: `meshmonitor.db`)

### Example Configuration

Create a `.env` file in the project root:

```bash
MQTT_BROKER_HOST=mqtt.example.com
MQTT_BROKER_PORT=1883
MQTT_TOPIC=msh/US/#
FLASK_PORT=8080
```

## Usage

### Running the Application

Start the application with:

```bash
python main.py
```

Or make it executable:

```bash
chmod +x main.py
./main.py
```

### Accessing the Web Interface

Once running, open your web browser and navigate to:

```
http://localhost:5000
```

### Application Components

The application consists of three main components running together:

1. **MQTT Client**: Subscribes to Meshtastic MQTT topics and receives messages
2. **Database**: Stores messages and node information in SQLite
3. **Web Server**: Serves the web interface and provides REST API endpoints

## Web Interface

The web interface is divided into three main sections:

### 1. Nodes Panel (Left)
- Lists all nodes that have sent messages
- Shows message count and last seen time for each node
- Click on a node to filter messages and zoom to its location on the map
- Search/filter nodes by ID

### 2. Map Panel (Center)
- Interactive map showing all message locations
- Click on markers to see message details
- Automatically zooms to show all markers
- Uses OpenStreetMap tiles (no API key required)

### 3. Messages Panel (Right)
- Displays received messages in chronological order
- Shows message type, payload, sender, and metadata
- Filter messages by node using the dropdown
- Messages with location data are highlighted in green
- Auto-refreshes every 10 seconds

### Statistics Bar
- **Total Messages**: Total number of messages received
- **Active Nodes**: Number of unique nodes that have sent messages
- **Messages with Location**: Number of messages containing GPS coordinates

## REST API Endpoints

The application provides the following REST API endpoints:

### Get Messages
```
GET /api/messages?limit=100&offset=0&node_id=!abc123
```

### Get Nodes
```
GET /api/nodes
```

### Get Messages with Locations
```
GET /api/messages/locations
```

### Get Statistics
```
GET /api/stats
```

### Health Check
```
GET /api/health
```

## Database Schema

### Messages Table
- `id`: Primary key
- `message_id`: Meshtastic message ID
- `from_node`: Sender node ID
- `to_node`: Recipient node ID
- `channel`: Channel number
- `packet_type`: Type of packet (TEXT_MESSAGE, POSITION, etc.)
- `payload`: Message payload/content
- `latitude`, `longitude`, `altitude`: GPS coordinates
- `snr`, `rssi`: Signal quality metrics
- `hop_limit`, `hop_start`: Routing information
- `received_at`: Timestamp when message was received
- `raw_data`: Original JSON payload

### Nodes Table
- `node_id`: Node identifier (primary key)
- `long_name`, `short_name`: Node names
- `hardware_model`: Device hardware model
- `last_seen`: Last message timestamp
- `last_latitude`, `last_longitude`: Last known position
- `message_count`: Total messages from this node

## File Structure

```
meshmonitor/
├── main.py                 # Main application entry point
├── config.py              # Configuration settings
├── database.py            # Database management
├── mqtt_broker.py         # MQTT client
├── meshtastic_parser.py   # Message parsing logic
├── api_server.py          # Flask REST API
├── requirements.txt       # Python dependencies
├── README.md             # This file
├── .gitignore            # Git ignore rules
└── static/               # Frontend files
    ├── index.html        # Main HTML page
    ├── style.css         # Styles
    └── app.js            # Frontend JavaScript
```

## Development

### Adding New Features

The application is designed to be easily extensible:

- **New message types**: Add parsing logic in `meshtastic_parser.py`
- **New API endpoints**: Add routes in `api_server.py`
- **Database schema changes**: Modify `database.py` and run migrations
- **UI enhancements**: Edit files in the `static/` directory

### Running in Development Mode

Set the Flask debug mode:

```bash
export FLASK_DEBUG=true
python main.py
```

## Troubleshooting

### MQTT Connection Issues

- Verify MQTT broker is running and accessible
- Check firewall settings
- Verify MQTT topic matches your Meshtastic configuration

### No Messages Appearing

- Ensure Meshtastic devices are publishing to MQTT
- Check MQTT topic subscription pattern
- Verify MQTT broker credentials if authentication is required

### Database Errors

- Check file permissions for database file
- Ensure sufficient disk space
- Delete `meshmonitor.db` to reset the database

## Production Deployment

For production deployment:

1. Use a proper MQTT broker (e.g., Mosquitto)
2. Set up a reverse proxy (e.g., nginx)
3. Use a process manager (e.g., systemd, supervisor)
4. Enable HTTPS for the web interface
5. Set `FLASK_DEBUG=false`
6. Consider using PostgreSQL for larger deployments

### Example systemd Service

Create `/etc/systemd/system/meshmonitor.service`:

```ini
[Unit]
Description=Meshtastic MQTT Monitor
After=network.target

[Service]
Type=simple
User=meshmonitor
WorkingDirectory=/opt/meshmonitor
Environment="MQTT_BROKER_HOST=localhost"
Environment="FLASK_PORT=5000"
ExecStart=/opt/meshmonitor/venv/bin/python main.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable meshmonitor
sudo systemctl start meshmonitor
```

## Contributing

Future enhancements:

- [ ] WebSocket support for real-time updates
- [ ] Message filtering by type
- [ ] Export messages to CSV/JSON
- [ ] Configurable map tile providers
- [ ] User authentication
- [ ] Message search functionality
- [ ] Telemetry graphs and charts
- [ ] Node information editing
- [ ] Custom node icons on map

## License

This project is open source and available for use and modification.

## Acknowledgments

- [Meshtastic](https://meshtastic.org/) - Long-range mesh communication platform
- [Leaflet](https://leafletjs.com/) - Open-source mapping library
- [Paho MQTT](https://www.eclipse.org/paho/) - MQTT client library
- [Flask](https://flask.palletsprojects.com/) - Python web framework
