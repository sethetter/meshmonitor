# Deploying Meshtastic MQTT Monitor on DigitalOcean

Complete step-by-step guide for deploying your Meshtastic MQTT Monitor on DigitalOcean with Docker, domain name, and SSL certificate.

## Prerequisites

- DigitalOcean account ([Sign up here](https://www.digitalocean.com/))
- Domain name (can be registered through DigitalOcean or any registrar)
- Local terminal or SSH client
- GitHub repository cloned locally

---

## Step 1: Create a DigitalOcean Droplet

### 1.1 Log into DigitalOcean
1. Go to [DigitalOcean](https://cloud.digitalocean.com/)
2. Click **"Create"** → **"Droplets"**

### 1.2 Choose Droplet Configuration

**Image:**
- Select **Ubuntu 22.04 LTS** (recommended)

**Droplet Size:**
- **Basic Plan**: $6/month (1 GB RAM, 1 vCPU, 25 GB SSD)
- **Recommended**: $12/month (2 GB RAM, 1 vCPU, 50 GB SSD) for better performance

**Datacenter Region:**
- Choose closest to your Meshtastic devices
- Example: New York, San Francisco, London, etc.

**Authentication:**
- **Option 1 (Recommended)**: SSH Key
  - Click "New SSH Key"
  - Paste your public key (`cat ~/.ssh/id_rsa.pub`)
  - Give it a name
- **Option 2**: Password (you'll receive it via email)

**Hostname:**
- Give it a memorable name: `meshtastic-monitor`

**Additional Options:**
- ✅ Check "Monitoring" (free)
- ❌ Skip backups initially (can enable later)

### 1.3 Create Droplet
1. Click **"Create Droplet"**
2. Wait 1-2 minutes for creation
3. **Note the IP address** (e.g., `167.99.123.45`)

---

## Step 2: Configure Your Domain

### Option A: Using DigitalOcean DNS (Recommended)

#### 2.1 Add Domain to DigitalOcean
1. Go to **Networking** → **Domains**
2. Click **"Add Domain"**
3. Enter your domain: `yourdomain.com`
4. Click **"Add Domain"**

#### 2.2 Create DNS Records
1. Add an **A Record**:
   - **Hostname**: `mesh` (creates mesh.yourdomain.com)
   - **Will Direct To**: Select your droplet
   - **TTL**: 3600 (1 hour)
   - Click **"Create Record"**

2. (Optional) Add another A Record for root domain:
   - **Hostname**: `@`
   - **Will Direct To**: Select your droplet
   - **TTL**: 3600

#### 2.3 Update Domain Nameservers
If your domain is registered elsewhere, update nameservers to:
```
ns1.digitalocean.com
ns2.digitalocean.com
ns3.digitalocean.com
```

**Note:** DNS propagation can take 24-48 hours, but usually takes 15-30 minutes.

### Option B: Using External DNS Provider

1. Log into your DNS provider (Cloudflare, Namecheap, etc.)
2. Create an **A Record**:
   - **Name**: `mesh`
   - **Type**: `A`
   - **Value**: Your droplet IP address
   - **TTL**: Automatic or 3600

---

## Step 3: Connect to Your Droplet

### 3.1 SSH into Droplet

Using SSH key:
```bash
ssh root@167.99.123.45
# Replace with your droplet IP
```

Using password:
```bash
ssh root@167.99.123.45
# Enter password from email
```

### 3.2 Update System

```bash
# Update package list
apt update

# Upgrade packages
apt upgrade -y

# Reboot if kernel was updated
reboot
```

Wait 1 minute, then reconnect:
```bash
ssh root@167.99.123.45
```

---

## Step 4: Install Docker

### 4.1 Install Docker Engine

```bash
# Install required packages
apt install -y ca-certificates curl gnupg lsb-release

# Add Docker's official GPG key
mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# Set up Docker repository
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker
apt update
apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Verify installation
docker --version
docker compose version
```

### 4.2 Start Docker

```bash
# Enable Docker to start on boot
systemctl enable docker

# Start Docker service
systemctl start docker

# Verify Docker is running
systemctl status docker
```

---

## Step 5: Configure Firewall

### 5.1 Set Up UFW (Uncomplicated Firewall)

```bash
# Allow SSH (IMPORTANT - do this first!)
ufw allow 22/tcp

# Allow HTTP and HTTPS
ufw allow 80/tcp
ufw allow 443/tcp

# Allow MQTT ports
ufw allow 8883/tcp

# Allow WebSocket (optional)
ufw allow 9001/tcp

# Enable firewall
ufw --force enable

# Check status
ufw status verbose
```

**Expected output:**
```
Status: active

To                         Action      From
--                         ------      ----
22/tcp                     ALLOW       Anywhere
80/tcp                     ALLOW       Anywhere
443/tcp                    ALLOW       Anywhere
8883/tcp                   ALLOW       Anywhere
9001/tcp                   ALLOW       Anywhere
```

---

## Step 6: Clone and Deploy Application

### 6.1 Clone Repository

```bash
# Install git if needed
apt install -y git

# Navigate to home directory
cd /root

# Clone the repository
git clone https://github.com/yourusername/meshmonitor.git
cd meshmonitor
```

### 6.2 Create Production Configuration

```bash
# Copy example environment file
cp .env.example .env

# Edit configuration (optional)
nano .env
```

Default `.env` should work, but you can customize:
```bash
MQTT_BROKER_HOST=mosquitto
MQTT_BROKER_PORT=1883
MQTT_TOPIC=msh/#
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
FLASK_DEBUG=False
DATABASE_PATH=/app/data/meshmonitor.db
```

Save and exit (Ctrl+X, then Y, then Enter)

### 6.3 Start Services (HTTP Only)

First, let's start without SSL to verify everything works:

```bash
# Start services
docker compose up -d

# Check logs
docker compose logs -f
```

**Look for these messages:**
```
meshmonitor-mosquitto  | mosquitto version ... starting
meshmonitor-app        | Starting Meshtastic MQTT Monitor
meshmonitor-app        | MQTT client started successfully
meshmonitor-app        | API server started successfully
```

Press `Ctrl+C` to exit logs.

### 6.4 Test HTTP Access

Visit in your browser:
- `http://YOUR_DROPLET_IP:8080`
- `http://mesh.yourdomain.com:8080` (if DNS has propagated)

You should see the Meshtastic MQTT Monitor interface!

---

## Step 7: Set Up SSL Certificate with Let's Encrypt

### 7.1 Verify DNS Propagation

Before getting SSL certificate, ensure DNS is working:

```bash
# Test DNS resolution
dig mesh.yourdomain.com

# Should show your droplet IP in the ANSWER section
```

Or test from your local computer:
```bash
ping mesh.yourdomain.com
```

### 7.2 Stop Nginx Container

```bash
# Stop all services temporarily
docker compose -f docker-compose.prod.yml down 2>/dev/null || true
docker compose down
```

### 7.3 Install Certbot

```bash
# Install Certbot
apt install -y certbot

# Obtain certificate
certbot certonly --standalone -d mesh.yourdomain.com --non-interactive --agree-tos -m your-email@example.com
```

**Replace:**
- `mesh.yourdomain.com` with your actual domain
- `your-email@example.com` with your email

**Expected output:**
```
Successfully received certificate.
Certificate is saved at: /etc/letsencrypt/live/mesh.yourdomain.com/fullchain.pem
Key is saved at:         /etc/letsencrypt/live/mesh.yourdomain.com/privkey.pem
```

### 7.4 Configure Nginx for SSL

Edit the nginx configuration:

```bash
nano nginx/nginx.conf
```

Find the HTTPS server block (around line 30) and uncomment it. Update with your domain:

```nginx
# Uncomment this section and update domain name:

server {
    listen 443 ssl http2;
    server_name mesh.yourdomain.com;  # UPDATE THIS

    ssl_certificate /etc/letsencrypt/live/mesh.yourdomain.com/fullchain.pem;  # UPDATE THIS
    ssl_certificate_key /etc/letsencrypt/live/mesh.yourdomain.com/privkey.pem;  # UPDATE THIS

    # SSL Configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    location / {
        proxy_pass http://app:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

Also uncomment the HTTP redirect (around line 15):

```nginx
server {
    listen 80;
    server_name mesh.yourdomain.com;  # UPDATE THIS
    return 301 https://$server_name$request_uri;  # UNCOMMENT THIS
}
```

Save and exit (Ctrl+X, then Y, then Enter).

### 7.5 Start Production Services

```bash
# Start with production configuration
docker compose -f docker-compose.prod.yml up -d

# Check logs
docker compose -f docker-compose.prod.yml logs -f
```

### 7.6 Test HTTPS Access

Visit in your browser:
- `https://mesh.yourdomain.com` (should work with green padlock!)
- `http://mesh.yourdomain.com` (should redirect to HTTPS)

---

## Step 8: Configure MQTT Authentication (Optional but Recommended)

### 8.1 Create MQTT Password

```bash
# Enter the mosquitto container
docker compose -f docker-compose.prod.yml exec mosquitto sh

# Create password file (inside container)
mosquitto_passwd -c /mosquitto/config/passwd meshtastic_user

# You'll be prompted to enter password twice
# Choose a strong password!

# Exit container
exit
```

### 8.2 Update Mosquitto Configuration

```bash
# Edit mosquitto config
nano mosquitto/config/mosquitto.conf
```

Change `allow_anonymous true` to `false` for public listeners:

```conf
# Listener for internal Docker network (keep anonymous)
listener 1883
allow_anonymous true

# Listener for Meshtastic devices (enable auth)
listener 8883
protocol mqtt
allow_anonymous false  # CHANGE THIS
password_file /mosquitto/config/passwd  # ADD THIS

# WebSocket listener (enable auth)
listener 9001
protocol websockets
allow_anonymous false  # CHANGE THIS
password_file /mosquitto/config/passwd  # ADD THIS
```

Save and exit.

### 8.3 Restart Mosquitto

```bash
docker compose -f docker-compose.prod.yml restart mosquitto

# Check logs
docker compose -f docker-compose.prod.yml logs mosquitto
```

---

## Step 9: Configure Meshtastic Devices

### 9.1 Using Meshtastic CLI

```bash
meshtastic --set mqtt.enabled true
meshtastic --set mqtt.address mesh.yourdomain.com
meshtastic --set mqtt.port 8883
meshtastic --set mqtt.username meshtastic_user
meshtastic --set mqtt.password YOUR_PASSWORD
meshtastic --set mqtt.encryption_enabled false
```

### 9.2 Using Meshtastic Mobile App

1. Open Meshtastic app
2. Connect to your device
3. Go to **Settings** → **MQTT**
4. Configure:
   - **Enabled**: ✅ ON
   - **MQTT Server Address**: `mesh.yourdomain.com`
   - **MQTT Server Port**: `8883`
   - **Username**: `meshtastic_user` (if authentication enabled)
   - **Password**: Your password
   - **Encryption Enabled**: ❌ OFF
   - **JSON Enabled**: ✅ ON (recommended)
5. Tap **Save**
6. Reboot device

---

## Step 10: Verify Everything Works

### 10.1 Check Services

```bash
# View all running containers
docker compose -f docker-compose.prod.yml ps

# Should show:
# - meshmonitor-app (healthy)
# - meshmonitor-mosquitto (healthy)
# - meshmonitor-nginx (running)
```

### 10.2 Test MQTT Connection

```bash
# Install mosquitto clients on droplet
apt install -y mosquitto-clients

# Subscribe to all topics (from outside container)
mosquitto_sub -h localhost -p 8883 -t 'msh/#' -v -u meshtastic_user -P YOUR_PASSWORD

# Leave this running and send a message from your Meshtastic device
# You should see messages appear here!
```

### 10.3 Check Web Interface

1. Open browser: `https://mesh.yourdomain.com`
2. You should see:
   - Statistics at top (may be 0 initially)
   - Empty nodes list (left)
   - Map (center)
   - Empty messages list (right)

3. Send a message from Meshtastic device
4. Refresh page - should see:
   - Message count increase
   - Node appear in left panel
   - Message in right panel

---

## Step 11: Set Up Automatic Certificate Renewal

### 11.1 Test Renewal

```bash
# Stop nginx temporarily for renewal test
docker compose -f docker-compose.prod.yml stop nginx

# Test renewal
certbot renew --dry-run

# If successful, restart nginx
docker compose -f docker-compose.prod.yml start nginx
```

### 11.2 Create Renewal Script

```bash
# Create renewal script
cat > /root/renew-cert.sh << 'EOF'
#!/bin/bash
cd /root/meshmonitor
docker compose -f docker-compose.prod.yml stop nginx
certbot renew --quiet
docker compose -f docker-compose.prod.yml start nginx
EOF

# Make executable
chmod +x /root/renew-cert.sh
```

### 11.3 Schedule Automatic Renewal

```bash
# Add to crontab (runs at 2 AM on first day of every month)
(crontab -l 2>/dev/null; echo "0 2 1 * * /root/renew-cert.sh >> /var/log/certbot-renew.log 2>&1") | crontab -

# Verify crontab
crontab -l
```

---

## Step 12: Enable Automatic Database Backups

### 12.1 Create Backup Script

```bash
# Create backup script
cat > /root/backup-meshmonitor.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/root/meshmonitor-backups"
mkdir -p $BACKUP_DIR
DATE=$(date +%Y%m%d_%H%M%S)
cd /root/meshmonitor
docker compose -f docker-compose.prod.yml exec -T app cat /app/data/meshmonitor.db > "$BACKUP_DIR/meshmonitor_$DATE.db"
# Keep only last 30 days of backups
find $BACKUP_DIR -name "meshmonitor_*.db" -mtime +30 -delete
echo "Backup completed: meshmonitor_$DATE.db"
EOF

# Make executable
chmod +x /root/backup-meshmonitor.sh
```

### 12.2 Schedule Daily Backups

```bash
# Add to crontab (daily at 3 AM)
(crontab -l 2>/dev/null; echo "0 3 * * * /root/backup-meshmonitor.sh >> /var/log/meshmonitor-backup.log 2>&1") | crontab -

# Verify
crontab -l
```

### 12.3 Test Backup

```bash
# Run backup manually
/root/backup-meshmonitor.sh

# Check backup was created
ls -lh /root/meshmonitor-backups/
```

---

## Maintenance Commands

### View Logs

```bash
# All services
docker compose -f docker-compose.prod.yml logs -f

# Specific service
docker compose -f docker-compose.prod.yml logs -f app
docker compose -f docker-compose.prod.yml logs -f mosquitto
docker compose -f docker-compose.prod.yml logs -f nginx
```

### Restart Services

```bash
# Restart all
docker compose -f docker-compose.prod.yml restart

# Restart specific service
docker compose -f docker-compose.prod.yml restart app
```

### Update Application

```bash
cd /root/meshmonitor

# Pull latest changes
git pull

# Rebuild and restart
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml up -d
```

### Check Resource Usage

```bash
# Droplet resources
htop  # Press 'q' to exit

# Docker resources
docker stats

# Disk usage
df -h
du -sh /root/meshmonitor/data/
```

### Database Maintenance

```bash
# View database size
docker compose -f docker-compose.prod.yml exec app du -sh /app/data/meshmonitor.db

# Access database shell
docker compose -f docker-compose.prod.yml exec app sqlite3 /app/data/meshmonitor.db

# Inside SQLite shell:
SELECT COUNT(*) FROM messages;
SELECT COUNT(*) FROM nodes;
.exit
```

---

## Troubleshooting

### DNS Not Working

```bash
# Check DNS from droplet
dig mesh.yourdomain.com

# Should show your droplet IP
# If not, wait longer for propagation or check DNS settings
```

### SSL Certificate Issues

```bash
# Check certificate
certbot certificates

# Force renew
certbot renew --force-renewal
```

### Can't Connect to MQTT

```bash
# Test locally
docker compose -f docker-compose.prod.yml exec mosquitto mosquitto_sub -h localhost -t 'msh/#' -v

# Check firewall
ufw status
ufw allow 8883/tcp

# Check mosquitto logs
docker compose -f docker-compose.prod.yml logs mosquitto
```

### Services Won't Start

```bash
# Check what's using ports
netstat -tulpn | grep -E ':(80|443|8883|1883|9001)'

# Check Docker status
systemctl status docker

# Restart everything
docker compose -f docker-compose.prod.yml down
docker compose -f docker-compose.prod.yml up -d
```

### High Memory Usage

```bash
# Check Docker memory
docker stats

# Restart if needed
docker compose -f docker-compose.prod.yml restart

# Consider upgrading droplet size
```

---

## Cost Summary

**Monthly Costs:**
- Droplet: $6-12/month
- Domain: ~$12/year ($1/month)
- SSL Certificate: $0 (Let's Encrypt is free!)
- **Total: ~$7-13/month**

**One-Time Costs:**
- Domain registration: ~$12/year (if you don't have one)

---

## Next Steps

✅ Your Meshtastic MQTT Monitor is now running on DigitalOcean!

**Access your monitor:**
- **Web Interface**: https://mesh.yourdomain.com
- **MQTT Broker**: mesh.yourdomain.com:8883

**Recommended:**
1. Set up monitoring alerts in DigitalOcean dashboard
2. Enable droplet backups ($1.20/month)
3. Set up a swap file if using 1GB RAM droplet
4. Configure fail2ban for additional security

**Optional Enhancements:**
- Add multiple domains (e.g., www.mesh.yourdomain.com)
- Set up monitoring with Grafana
- Configure email alerts for system issues
- Add Cloudflare for DDoS protection

---

## Support

Having issues? Check:
1. Logs: `docker compose -f docker-compose.prod.yml logs -f`
2. DigitalOcean Community: https://www.digitalocean.com/community
3. Meshtastic Discord: https://discord.gg/meshtastic
4. GitHub Issues: https://github.com/yourusername/meshmonitor/issues
