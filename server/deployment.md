# Perfect Number Network - Production Deployment Guide

This guide covers deploying the Perfect Number Network to production environments.

## 🚀 Quick Deployment Options

### Option 1: Single Server (Recommended for Small Networks)

**Best for:** Personal use, small teams (1-10 clients)

```bash
# On a Linux server (Ubuntu 22.04 recommended)
git clone <repository>
cd perfectnet
./setup.sh
python server.py --host 0.0.0.0 --port 5000
python dashboard.py --host 0.0.0.0 --port 8080
```

### Option 2: Docker Deployment (Easiest)

**Best for:** Quick setup, containerized environments

```bash
# Clone repository
git clone <repository>
cd perfectnet

# Start with Docker Compose
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

Access:
- Server: `http://localhost:5000`
- Dashboard: `http://localhost:8080`

### Option 3: Systemd Services (Best for Production)

**Best for:** Production Linux servers, high availability

See detailed instructions below.

## 📦 Production Setup on Linux (Ubuntu/Debian)

### Step 1: System Preparation

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y python3 python3-pip python3-venv git \
    libgmp-dev libmpfr-dev libmpc-dev gcc g++ nginx certbot python3-certbot-nginx

# Create dedicated user
sudo useradd -r -m -s /bin/bash perfectnet
sudo mkdir -p /opt/perfectnet /var/lib/perfectnet
sudo chown perfectnet:perfectnet /var/lib/perfectnet
```

### Step 2: Application Installation

```bash
# Clone repository as perfectnet user
sudo su - perfectnet
cd /opt/perfectnet
git clone <repository> .

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Initialize database
python -c "from server import init_database; init_database()"

# Exit perfectnet user
exit
```

### Step 3: Systemd Service Setup

```bash
# Copy service files
sudo cp systemd/perfectnet-server.service /etc/systemd/system/
sudo cp systemd/perfectnet-dashboard.service /etc/systemd/system/

# Update service files if needed (edit paths, user, etc.)
sudo nano /etc/systemd/system/perfectnet-server.service
sudo nano /etc/systemd/system/perfectnet-dashboard.service

# Reload systemd
sudo systemctl daemon-reload

# Enable services
sudo systemctl enable perfectnet-server
sudo systemctl enable perfectnet-dashboard

# Start services
sudo systemctl start perfectnet-server
sudo systemctl start perfectnet-dashboard

# Check status
sudo systemctl status perfectnet-server
sudo systemctl status perfectnet-dashboard
```

### Step 4: Nginx Reverse Proxy

```bash
# Copy nginx configuration
sudo cp nginx.conf /etc/nginx/sites-available/perfectnet

# Edit configuration (update domain name)
sudo nano /etc/nginx/sites-available/perfectnet

# Enable site
sudo ln -s /etc/nginx/sites-available/perfectnet /etc/nginx/sites-enabled/

# Test configuration
sudo nginx -t

# Reload nginx
sudo systemctl reload nginx
```

### Step 5: SSL Certificate (Let's Encrypt)

```bash
# Get SSL certificate
sudo certbot --nginx -d perfectnet.example.com

# Test auto-renewal
sudo certbot renew --dry-run
```

### Step 6: Firewall Configuration

```bash
# Configure UFW
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable

# Optionally block direct access to Flask ports
# (only allow via nginx)
sudo ufw deny 5000/tcp
sudo ufw deny 8080/tcp
```

## 🐳 Docker Production Deployment

### Using Docker Compose

Create `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  server:
    build: .
    container_name: perfectnet-server
    restart: always
    ports:
      - "127.0.0.1:5000:5000"  # Only localhost access
    volumes:
      - ./data:/app/data
    environment:
      - DB_FILE=/app/data/perfectnet.db
    command: python server.py --host 0.0.0.0 --port 5000 --db /app/data/perfectnet.db
    networks:
      - perfectnet
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  dashboard:
    build: .
    container_name: perfectnet-dashboard
    restart: always
    ports:
      - "127.0.0.1:8080:8080"  # Only localhost access
    environment:
      - API_URL=http://server:5000
    command: python dashboard.py --host 0.0.0.0 --port 8080 --api-url http://server:5000
    depends_on:
      - server
    networks:
      - perfectnet
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  nginx:
    image: nginx:alpine
    container_name: perfectnet-nginx
    restart: always
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx-docker.conf:/etc/nginx/conf.d/default.conf:ro
      - ./certs:/etc/nginx/certs:ro
    depends_on:
      - server
      - dashboard
    networks:
      - perfectnet

networks:
  perfectnet:
    driver: bridge

volumes:
  data:
```

Deploy:

```bash
docker-compose -f docker-compose.prod.yml up -d
```

## ☁️ Cloud Platform Deployments

### AWS EC2

1. **Launch Instance**:
   - Ubuntu 22.04 LTS
   - t3.medium or larger
   - 20GB storage minimum
   - Security Group: Allow ports 22, 80, 443

2. **Connect and Setup**:
   ```bash
   ssh -i your-key.pem ubuntu@your-ec2-ip
   git clone <repository>
   cd perfectnet
   ./setup.sh
   ```

3. **Follow Linux production setup** steps above

4. **Configure Elastic IP** for static IP address

### DigitalOcean Droplet

1. **Create Droplet**:
   - Ubuntu 22.04
   - 2GB RAM minimum
   - Choose datacenter region

2. **Initial Setup**:
   ```bash
   ssh root@your-droplet-ip
   apt update && apt upgrade -y
   ```

3. **Follow Linux production setup** steps above

4. **Use DigitalOcean's DNS** to point domain to droplet

### Google Cloud Platform (GCP)

1. **Create Compute Engine Instance**:
   - Ubuntu 22.04 LTS
   - e2-medium or larger
   - Allow HTTP and HTTPS traffic

2. **Setup**:
   ```bash
   gcloud compute ssh your-instance-name
   ```

3. **Follow Linux production setup** steps above

### Heroku (Not Recommended)

Heroku's free tier is limited and not ideal for this application due to:
- No persistent storage (database resets)
- 30-minute sleep timeout
- Limited compute resources

## 🔒 Security Best Practices

### 1. Use Strong API Keys

API keys are automatically generated securely using `secrets.token_urlsafe(32)`.

### 2. Enable HTTPS

Always use SSL/TLS in production:
```bash
sudo certbot --nginx -d perfectnet.example.com
```

### 3. Firewall Configuration

```bash
# Only allow necessary ports
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### 4. Regular Updates

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Update Python packages
cd /opt/perfectnet
source venv/bin/activate
pip install --upgrade -r requirements.txt
```

### 5. Database Backups

```bash
# Create backup script
cat > /opt/perfectnet/backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/var/backups/perfectnet"
mkdir -p $BACKUP_DIR
DATE=$(date +%Y%m%d_%H%M%S)
cp /var/lib/perfectnet/perfectnet.db "$BACKUP_DIR/perfectnet_$DATE.db"
# Keep only last 30 days
find $BACKUP_DIR -name "perfectnet_*.db" -mtime +30 -delete
EOF

chmod +x /opt/perfectnet/backup.sh

# Add to cron (daily at 2 AM)
(crontab -l 2>/dev/null; echo "0 2 * * * /opt/perfectnet/backup.sh") | crontab -
```

### 6. Log Rotation

```bash
# Create logrotate config
sudo cat > /etc/logrotate.d/perfectnet << 'EOF'
/var/log/perfectnet/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 perfectnet perfectnet
    sharedscripts
    postrotate
        systemctl reload perfectnet-server > /dev/null 2>&1 || true
        systemctl reload perfectnet-dashboard > /dev/null 2>&1 || true
    endscript
}
EOF
```

## 📊 Monitoring

### Health Checks

```bash
# Check server health
curl http://localhost:5000/api/health

# Check dashboard health
curl http://localhost:8080/health
```

### Service Status

```bash
# View service status
sudo systemctl status perfectnet-server
sudo systemctl status perfectnet-dashboard

# View logs
sudo journalctl -u perfectnet-server -f
sudo journalctl -u perfectnet-dashboard -f
```

### Resource Monitoring

```bash
# Install htop
sudo apt install htop

# Monitor resources
htop

# Check disk usage
df -h
du -sh /var/lib/perfectnet/
```

### Automated Monitoring (Optional)

Use monitoring tools like:
- **Prometheus + Grafana**: Metrics and dashboards
- **Uptime Kuma**: Simple uptime monitoring
- **Netdata**: Real-time performance monitoring

## 🔄 Updates and Maintenance

### Updating the Application

```bash
# As perfectnet user
sudo su - perfectnet
cd /opt/perfectnet

# Pull latest changes
git pull

# Update dependencies
source venv/bin/activate
pip install --upgrade -r requirements.txt

# Restart services
exit
sudo systemctl restart perfectnet-server
sudo systemctl restart perfectnet-dashboard
```

### Database Maintenance

```bash
# Vacuum database (optimize)
python admin.py vacuum

# View statistics
python admin.py stats

# Reset expired assignments
python admin.py reset
```

## 🆘 Troubleshooting

### Services won't start

```bash
# Check service logs
sudo journalctl -u perfectnet-server -n 50
sudo journalctl -u perfectnet-dashboard -n 50

# Check if ports are in use
sudo lsof -i :5000
sudo lsof -i :8080

# Verify file permissions
ls -la /opt/perfectnet/
ls -la /var/lib/perfectnet/
```

### High CPU usage

```bash
# Check running processes
ps aux | grep python

# Check active assignments
python monitor.py

# Consider limiting concurrent assignments
```

### Database locked errors

```bash
# Check for multiple processes accessing database
ps aux | grep server.py

# Restart services
sudo systemctl restart perfectnet-server
```

## 📈 Scaling

### Horizontal Scaling

For larger networks (50+ clients), consider:

1. **Separate Database Server**: Use PostgreSQL instead of SQLite
2. **Load Balancing**: Multiple server instances behind load balancer
3. **Redis Caching**: Cache frequently accessed data
4. **CDN**: Serve dashboard static assets via CDN

### Vertical Scaling

Increase server resources:
- CPU: More cores for parallel processing
- RAM: Larger database cache
- SSD: Faster database access

## 📞 Support

For issues, check:
1. Service logs: `sudo journalctl -u perfectnet-server`
2. Nginx logs: `/var/log/nginx/`
3. Application health: `curl http://localhost:5000/api/health`
4. Database: `python admin.py stats`
