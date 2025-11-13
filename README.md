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

## Docker Deployment

The easiest way to deploy Meshtastic MQTT Monitor is using Docker. This method bundles all dependencies and services into containers.

### Quick Start with Docker

#### Prerequisites

- Docker Engine 20.10+ ([Install Docker](https://docs.docker.com/get-docker/))
- Docker Compose 2.0+ (usually included with Docker Desktop)

#### Development Deployment

For local development or testing:

```bash
# Clone the repository
git clone https://github.com/yourusername/meshmonitor.git
cd meshmonitor

# Start all services (app + mosquitto MQTT broker)
./docker-run.sh up

# Or manually with docker-compose
docker-compose up -d
```

The application will be available at:
- **Web Interface**: http://localhost:5000
- **MQTT Broker**: localhost:1883 (internal) / localhost:8883 (external)
- **WebSocket**: ws://localhost:9001

#### Production Deployment with Docker

For production deployment on a public server:

```bash
# Clone the repository
git clone https://github.com/yourusername/meshmonitor.git
cd meshmonitor

# Start production services (app + mosquitto + nginx)
sudo ./docker-prod.sh up

# Or manually with docker-compose
docker-compose -f docker-compose.prod.yml up -d
```

#### Docker Services

The Docker deployment includes three services:

1. **mosquitto** - Eclipse Mosquitto MQTT broker
   - Port 1883: Internal MQTT (for app communication)
   - Port 8883: External MQTT (for Meshtastic devices)
   - Port 9001: WebSocket MQTT

2. **app** - Meshtastic MQTT Monitor application
   - Port 5000: Flask web server and REST API

3. **nginx** - Reverse proxy (production only)
   - Port 80: HTTP (redirects to HTTPS in production)
   - Port 443: HTTPS

#### Docker Commands

```bash
# Start services
./docker-run.sh up
# or: docker-compose up -d

# Stop services
./docker-run.sh down
# or: docker-compose down

# View logs
./docker-run.sh logs
# or: docker-compose logs -f

# View logs for specific service
docker-compose logs -f app
docker-compose logs -f mosquitto

# Restart services
./docker-run.sh restart
# or: docker-compose restart

# Rebuild images after code changes
./docker-run.sh build
# or: docker-compose build

# Check service status
docker-compose ps
```

### Docker Configuration

#### Environment Variables

Create a `.env` file (or copy from `.env.example`):

```bash
MQTT_BROKER_HOST=mosquitto
MQTT_BROKER_PORT=1883
MQTT_TOPIC=msh/#
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
FLASK_DEBUG=False
DATABASE_PATH=/app/data/meshmonitor.db
```

#### MQTT Broker Configuration

Edit `mosquitto/config/mosquitto.conf` to customize the MQTT broker:

```conf
# Enable authentication
allow_anonymous false
password_file /mosquitto/config/passwd

# Configure listeners
listener 1883
listener 8883
listener 9001
protocol websockets
```

To create MQTT users:

```bash
# Enter the mosquitto container
docker-compose exec mosquitto sh

# Create a user (inside container)
mosquitto_passwd -c /mosquitto/config/passwd meshtastic_user

# Exit container
exit

# Restart mosquitto
docker-compose restart mosquitto
```

#### Nginx Configuration

For production with SSL, edit `nginx/nginx.conf`:

1. Update `server_name` with your domain
2. Uncomment HTTPS server block
3. Update SSL certificate paths
4. Enable HTTP to HTTPS redirect

```nginx
server {
    listen 443 ssl http2;
    server_name mesh.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/mesh.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/mesh.yourdomain.com/privkey.pem;

    # ... rest of configuration
}
```

### Docker Production Deployment with Domain

Complete steps for deploying to a public server:

#### 1. Set up your server

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo apt install docker-compose-plugin

# Clone repository
git clone https://github.com/yourusername/meshmonitor.git
cd meshmonitor
```

#### 2. Configure DNS

Point your domain to the server:
- Create an A record for `mesh.yourdomain.com` → your server IP

#### 3. Get SSL Certificate

```bash
# Install certbot
sudo apt install certbot

# Stop nginx temporarily if running
docker-compose -f docker-compose.prod.yml stop nginx

# Obtain certificate
sudo certbot certonly --standalone -d mesh.yourdomain.com

# Certificates will be in: /etc/letsencrypt/live/mesh.yourdomain.com/
```

#### 4. Update Configuration

Edit `nginx/nginx.conf`:
- Replace `mesh.yourdomain.com` with your domain
- Uncomment the HTTPS server block
- Ensure SSL certificate paths are correct

#### 5. Configure Firewall

```bash
# Allow required ports
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw allow 8883/tcp  # MQTT
sudo ufw allow 9001/tcp  # WebSocket (optional)
sudo ufw enable
```

#### 6. Start Services

```bash
# Start in production mode
sudo ./docker-prod.sh up

# Or manually
docker-compose -f docker-compose.prod.yml up -d
```

#### 7. Configure Meshtastic Devices

Point your Meshtastic devices to your server:

```bash
meshtastic --set mqtt.enabled true
meshtastic --set mqtt.address mesh.yourdomain.com
meshtastic --set mqtt.port 8883
meshtastic --set mqtt.username meshtastic_user  # if using auth
meshtastic --set mqtt.password your_password    # if using auth
```

### Docker Volumes and Persistence

Data is persisted in Docker volumes:

```bash
# View volumes
docker volume ls

# Backup database
docker-compose exec app cat /app/data/meshmonitor.db > backup.db

# Restore database
docker-compose exec -T app sh -c 'cat > /app/data/meshmonitor.db' < backup.db

# Access database directly
docker-compose exec app sqlite3 /app/data/meshmonitor.db
```

### Docker Troubleshooting

**Services won't start:**
```bash
# Check logs
docker-compose logs

# Check specific service
docker-compose logs app
docker-compose logs mosquitto
```

**Can't connect to MQTT:**
```bash
# Test MQTT from inside Docker network
docker-compose exec app sh -c "pip install paho-mqtt && python -c \"import paho.mqtt.client as mqtt; c = mqtt.Client(); c.connect('mosquitto', 1883); print('Connected')\""

# Test MQTT from host
mosquitto_sub -h localhost -p 8883 -t 'msh/#' -v
```

**Permission issues:**
```bash
# Fix permissions on data directories
sudo chown -R $USER:$USER data mosquitto
```

**Rebuild after code changes:**
```bash
docker-compose build --no-cache
docker-compose up -d
```

### Docker Advantages

✅ **Easy Setup** - One command deployment
✅ **Isolated Environment** - No dependency conflicts
✅ **Consistent** - Same environment everywhere
✅ **Includes MQTT Broker** - No separate Mosquitto installation
✅ **Production Ready** - Nginx reverse proxy included
✅ **Auto-restart** - Services restart on failure
✅ **Easy Updates** - Pull and rebuild
✅ **Portable** - Works on any Docker-compatible host

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

This section provides comprehensive instructions for deploying Meshtastic MQTT Monitor on a public host with a custom domain name.

### Overview

A production deployment typically includes:
- VPS or cloud server (Ubuntu/Debian recommended)
- Domain name pointed to your server
- Mosquitto MQTT broker
- Nginx reverse proxy with SSL/TLS
- Systemd service management
- Firewall configuration

### Prerequisites

- VPS with Ubuntu 20.04+ or Debian 11+ (minimum 1GB RAM recommended)
- Root or sudo access
- Domain name (e.g., `mesh.yourdomain.com`)
- DNS A record pointing to your server's IP address

### Step 1: Initial Server Setup

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y python3 python3-pip python3-venv git nginx certbot python3-certbot-nginx mosquitto mosquitto-clients

# Create a user for the application
sudo useradd -r -s /bin/bash -d /opt/meshmonitor -m meshmonitor

# Add your user to the meshmonitor group (for management)
sudo usermod -aG meshmonitor $USER
```

### Step 2: Install and Configure Mosquitto MQTT Broker

```bash
# Install Mosquitto
sudo apt install -y mosquitto mosquitto-clients

# Create Mosquitto configuration
sudo tee /etc/mosquitto/conf.d/meshmonitor.conf > /dev/null <<EOF
# Listener for local connections (Python app)
listener 1883 localhost
allow_anonymous true

# Listener for Meshtastic devices (public)
listener 8883
protocol mqtt

# Enable websockets (optional, for browser clients)
listener 9001
protocol websockets

# Persistence
persistence true
persistence_location /var/lib/mosquitto/

# Logging
log_dest file /var/log/mosquitto/mosquitto.log
log_type all

# Security - set to false initially, configure auth later
allow_anonymous true
EOF

# Restart Mosquitto
sudo systemctl restart mosquitto
sudo systemctl enable mosquitto

# Verify Mosquitto is running
sudo systemctl status mosquitto
```

### Step 3: Configure Firewall

```bash
# Allow SSH (if not already allowed)
sudo ufw allow 22/tcp

# Allow HTTP and HTTPS for web interface
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Allow MQTT port for Meshtastic devices
sudo ufw allow 8883/tcp

# Allow WebSocket (optional)
sudo ufw allow 9001/tcp

# Enable firewall
sudo ufw --force enable

# Check status
sudo ufw status
```

### Step 4: Clone and Setup Application

```bash
# Switch to meshmonitor user
sudo su - meshmonitor

# Clone the repository (or copy files)
git clone https://github.com/yourusername/meshmonitor.git /opt/meshmonitor
# Or if copying files:
# sudo cp -r /path/to/meshmonitor /opt/meshmonitor

# Navigate to directory
cd /opt/meshmonitor

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create production configuration
cat > .env <<EOF
MQTT_BROKER_HOST=localhost
MQTT_BROKER_PORT=1883
MQTT_TOPIC=msh/#
FLASK_HOST=127.0.0.1
FLASK_PORT=5000
FLASK_DEBUG=False
DATABASE_PATH=/opt/meshmonitor/data/meshmonitor.db
EOF

# Create data directory
mkdir -p /opt/meshmonitor/data

# Test the application
python main.py
# Press Ctrl+C after verifying it starts without errors

# Exit meshmonitor user
exit
```

### Step 5: Create Systemd Service

```bash
# Create systemd service file
sudo tee /etc/systemd/system/meshmonitor.service > /dev/null <<EOF
[Unit]
Description=Meshtastic MQTT Monitor
After=network.target mosquitto.service
Requires=mosquitto.service

[Service]
Type=simple
User=meshmonitor
Group=meshmonitor
WorkingDirectory=/opt/meshmonitor
Environment="PATH=/opt/meshmonitor/venv/bin"
EnvironmentFile=/opt/meshmonitor/.env
ExecStart=/opt/meshmonitor/venv/bin/python /opt/meshmonitor/main.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

# Security hardening
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/opt/meshmonitor/data

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd
sudo systemctl daemon-reload

# Enable and start the service
sudo systemctl enable meshmonitor
sudo systemctl start meshmonitor

# Check status
sudo systemctl status meshmonitor

# View logs
sudo journalctl -u meshmonitor -f
```

### Step 6: Configure Nginx Reverse Proxy

```bash
# Create Nginx configuration
sudo tee /etc/nginx/sites-available/meshmonitor > /dev/null <<'EOF'
server {
    listen 80;
    server_name mesh.yourdomain.com;  # Replace with your domain

    # Redirect HTTP to HTTPS (will be enabled after SSL setup)
    # return 301 https://$server_name$request_uri;

    # Proxy to Flask application
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket support (for future features)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # Increase timeouts for long-polling or WebSocket
    proxy_read_timeout 300s;
    proxy_connect_timeout 75s;
}
EOF

# Enable the site
sudo ln -s /etc/nginx/sites-available/meshmonitor /etc/nginx/sites-enabled/

# Test Nginx configuration
sudo nginx -t

# Restart Nginx
sudo systemctl restart nginx
```

### Step 7: Setup SSL/TLS with Let's Encrypt

```bash
# Obtain SSL certificate (replace with your domain and email)
sudo certbot --nginx -d mesh.yourdomain.com --non-interactive --agree-tos -m your-email@example.com

# Certbot automatically configures Nginx for HTTPS

# Test automatic renewal
sudo certbot renew --dry-run

# Setup automatic renewal (certbot usually does this automatically)
sudo systemctl status certbot.timer
```

After SSL setup, your Nginx configuration will be automatically updated. The final configuration should look like:

```nginx
server {
    listen 80;
    server_name mesh.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name mesh.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/mesh.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/mesh.yourdomain.com/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

### Step 8: Configure DNS

Point your domain to your server:

1. Log in to your domain registrar or DNS provider
2. Create an A record:
   - **Name**: `mesh` (or `@` for root domain)
   - **Type**: `A`
   - **Value**: Your server's public IP address
   - **TTL**: 3600 (or default)

3. Wait for DNS propagation (can take up to 48 hours, usually much faster)
4. Verify with: `dig mesh.yourdomain.com` or `nslookup mesh.yourdomain.com`

### Step 9: Secure Mosquitto with Authentication (Optional but Recommended)

```bash
# Create password file for MQTT users
sudo mosquitto_passwd -c /etc/mosquitto/passwd meshtastic_user

# Update Mosquitto configuration
sudo tee /etc/mosquitto/conf.d/meshmonitor.conf > /dev/null <<EOF
# Local listener (no auth needed for local app)
listener 1883 localhost
allow_anonymous true

# Public listener with authentication
listener 8883
protocol mqtt
allow_anonymous false
password_file /etc/mosquitto/passwd

# Websockets with authentication
listener 9001
protocol websockets
allow_anonymous false
password_file /etc/mosquitto/passwd

persistence true
persistence_location /var/lib/mosquitto/
log_dest file /var/log/mosquitto/mosquitto.log
log_type all
EOF

# Restart Mosquitto
sudo systemctl restart mosquitto
```

If using authentication, update your Meshtastic devices to use the credentials when connecting to the MQTT broker.

### Step 10: Configure Meshtastic Devices

On your Meshtastic device, configure MQTT settings:

**Using the Meshtastic CLI:**
```bash
meshtastic --set mqtt.enabled true
meshtastic --set mqtt.address mesh.yourdomain.com
meshtastic --set mqtt.port 8883
meshtastic --set mqtt.username meshtastic_user
meshtastic --set mqtt.password your_password
meshtastic --set mqtt.encryption_enabled false
```

**Using the Meshtastic App:**
1. Open the Meshtastic app
2. Go to Settings → MQTT
3. Enable MQTT
4. Set Server Address: `mesh.yourdomain.com`
5. Set Port: `8883`
6. Set Username: `meshtastic_user` (if using auth)
7. Set Password: `your_password` (if using auth)
8. Save settings

### Step 11: Monitoring and Maintenance

```bash
# View application logs
sudo journalctl -u meshmonitor -f

# View Mosquitto logs
sudo tail -f /var/log/mosquitto/mosquitto.log

# Check service status
sudo systemctl status meshmonitor
sudo systemctl status mosquitto
sudo systemctl status nginx

# Restart services if needed
sudo systemctl restart meshmonitor
sudo systemctl restart mosquitto
sudo systemctl restart nginx

# View database size
du -sh /opt/meshmonitor/data/meshmonitor.db

# Backup database
sudo -u meshmonitor cp /opt/meshmonitor/data/meshmonitor.db /opt/meshmonitor/data/meshmonitor.db.backup
```

### Step 12: Access Your Application

Your Meshtastic MQTT Monitor is now accessible at:
- **Web Interface**: `https://mesh.yourdomain.com`
- **MQTT Broker**: `mesh.yourdomain.com:8883`
- **WebSocket** (if enabled): `wss://mesh.yourdomain.com:9001`

### Security Best Practices

1. **Keep system updated:**
   ```bash
   sudo apt update && sudo apt upgrade -y
   ```

2. **Enable fail2ban for SSH protection:**
   ```bash
   sudo apt install fail2ban
   sudo systemctl enable fail2ban
   ```

3. **Use strong passwords for MQTT authentication**

4. **Regularly backup the database:**
   ```bash
   # Create a backup script
   sudo tee /opt/meshmonitor/backup.sh > /dev/null <<'EOF'
   #!/bin/bash
   BACKUP_DIR="/opt/meshmonitor/backups"
   mkdir -p $BACKUP_DIR
   DATE=$(date +%Y%m%d_%H%M%S)
   cp /opt/meshmonitor/data/meshmonitor.db "$BACKUP_DIR/meshmonitor_$DATE.db"
   # Keep only last 7 days of backups
   find $BACKUP_DIR -name "meshmonitor_*.db" -mtime +7 -delete
   EOF

   sudo chmod +x /opt/meshmonitor/backup.sh
   sudo chown meshmonitor:meshmonitor /opt/meshmonitor/backup.sh

   # Add to crontab (daily backup at 2 AM)
   (crontab -l 2>/dev/null; echo "0 2 * * * /opt/meshmonitor/backup.sh") | crontab -
   ```

5. **Monitor disk space:**
   ```bash
   df -h
   ```

6. **Set up log rotation:**
   ```bash
   sudo tee /etc/logrotate.d/meshmonitor > /dev/null <<EOF
   /var/log/meshmonitor/*.log {
       daily
       missingok
       rotate 14
       compress
       delaycompress
       notifempty
       create 0640 meshmonitor meshmonitor
   }
   EOF
   ```

### Troubleshooting Deployment

**Application won't start:**
```bash
sudo journalctl -u meshmonitor -n 50
```

**Can't connect to MQTT broker:**
```bash
# Test locally
mosquitto_sub -h localhost -t 'msh/#' -v

# Test remotely
mosquitto_sub -h mesh.yourdomain.com -p 8883 -t 'msh/#' -v -u meshtastic_user -P your_password
```

**Nginx errors:**
```bash
sudo nginx -t
sudo tail -f /var/log/nginx/error.log
```

**SSL certificate issues:**
```bash
sudo certbot certificates
sudo certbot renew --dry-run
```

**Firewall blocking connections:**
```bash
sudo ufw status verbose
sudo ufw allow 8883/tcp  # If MQTT port is blocked
```

### Performance Optimization

For high-traffic deployments:

1. **Use PostgreSQL instead of SQLite:**
   - Install PostgreSQL
   - Update `database.py` to use PostgreSQL
   - Update connection string in `.env`

2. **Enable Nginx caching:**
   ```nginx
   proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=api_cache:10m max_size=100m;

   location /api/ {
       proxy_cache api_cache;
       proxy_cache_valid 200 10s;
       # ... other proxy settings
   }
   ```

3. **Use Gunicorn or uWSGI instead of Flask development server:**
   ```bash
   pip install gunicorn
   # Update systemd ExecStart
   ExecStart=/opt/meshmonitor/venv/bin/gunicorn -w 4 -b 127.0.0.1:5000 api_server:app
   ```

### Scaling Considerations

For larger deployments:
- Use PostgreSQL for better concurrent access
- Deploy multiple application instances with load balancing
- Use Redis for caching and session management
- Consider containerization with Docker
- Set up monitoring with Prometheus and Grafana

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
