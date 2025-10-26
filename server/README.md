# Perfect Number Network

Distributed search system for discovering perfect numbers through the Euclid-Euler theorem. Find perfect numbers by testing Mersenne primes using the Lucas-Lehmer primality test.

## 🎯 Quick Start

### Prerequisites

- Python 3.8+
- 2GB RAM minimum
- Internet connection

### 30-Second Setup

```bash
# Clone repository
git clone https://github.com/yourusername/perfectnet.git
cd perfectnet

# Run automated setup
chmod +x setup.sh
./setup.sh

# Start services
./start.sh
```

Access dashboard at **http://localhost:8080**

### Manual Setup

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install flask flask-cors requests gmpy2

# Initialize database
python server.py --host 127.0.0.1 --port 5000 &
sleep 3
python -c "from server import init_database; init_database()"
pkill -f server.py

# Start server and dashboard
python server.py --host 0.0.0.0 --port 5000 &
python dashboard.py --host 0.0.0.0 --port 8080 &

# Start a client
python client.py --server http://localhost:5000 --username alice
```

## 📋 What This Does

Perfect numbers are integers equal to the sum of their proper divisors. For example:
- **6** = 1 + 2 + 3 (first perfect number)
- **28** = 1 + 2 + 4 + 7 + 14 (second perfect number)

The **Euclid-Euler theorem** states that every even perfect number has the form:

```
P = 2^(p-1) × (2^p - 1)
```

where `2^p - 1` is a Mersenne prime.

This system:
1. **Server** distributes Mersenne prime candidates to test
2. **Clients** run Lucas-Lehmer tests to verify primality
3. **Dashboard** shows real-time progress and discoveries

## 🚀 Deployment Scenarios

### 1. Local Development

Quick testing on your machine:

```bash
python server.py
python dashboard.py
python client.py --username dev
```

**Access**: http://localhost:8080

### 2. Local Network

Share with devices on your network:

```bash
# Get your local IP
ip addr show | grep "inet "

# Start services (listen on all interfaces)
python server.py --host 0.0.0.0 --port 5000
python dashboard.py --host 0.0.0.0 --port 8080 --api-url http://192.168.1.100:5000

# Access from other devices
# Dashboard: http://192.168.1.100:8080
# Client: python client.py --server http://192.168.1.100:5000 --username bob
```

### 3. Public Access with DuckDNS

Free dynamic DNS and SSL:

**Setup DuckDNS** (5 minutes):
```bash
# 1. Create account at https://www.duckdns.org
# 2. Create subdomain: myserver.duckdns.org
# 3. Install updater
mkdir ~/duckdns && cd ~/duckdns
echo 'url="https://www.duckdns.org/update?domains=SUBDOMAIN&token=TOKEN&ip=" | curl -k -o ~/duckdns/duck.log -K -' > duck.sh
chmod +x duck.sh
./duck.sh

# 4. Add to crontab
crontab -e
# Add: */5 * * * * ~/duckdns/duck.sh >/dev/null 2>&1
```

**Configure Server**:
```bash
# Install nginx and certbot
sudo apt install nginx certbot python3-certbot-nginx

# Copy nginx config
sudo cp nginx.conf /etc/nginx/sites-available/perfectnet
sudo nano /etc/nginx/sites-available/perfectnet
# Edit: server_name myserver.duckdns.org;

# Enable site
sudo ln -s /etc/nginx/sites-available/perfectnet /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

# Get SSL certificate
sudo certbot --nginx -d myserver.duckdns.org

# Install services
sudo cp perfectnet-*.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now perfectnet-server perfectnet-dashboard
```

**Port Forward on Router**:
- Port 80 → 192.168.1.100:80
- Port 443 → 192.168.1.100:443

**Access**: https://myserver.duckdns.org

### 4. Cloud Deployment (AWS/GCP/Azure)

**AWS EC2 Example**:

```bash
# Launch Ubuntu 22.04 instance (t2.small+)
# Security Group: Allow 22, 80, 443

# SSH into instance
ssh ubuntu@your-instance-ip

# Install
sudo apt update && sudo apt install -y python3 python3-pip nginx certbot python3-certbot-nginx
git clone https://github.com/yourusername/perfectnet.git
cd perfectnet
./setup.sh

# Point domain A record to Elastic IP
# Get SSL: sudo certbot --nginx -d perfectnet.example.com

# Start services
sudo systemctl start perfectnet-server perfectnet-dashboard
```

**Access**: https://perfectnet.example.com

### 5. Docker Deployment

Easy containerized deployment:

```bash
# Start everything with Docker Compose
docker-compose up -d

# View logs
docker-compose logs -f

# Access
# Dashboard: http://localhost:8080
# API: http://localhost:5000/api/health

# Scale server instances
docker-compose up -d --scale server=3

# Stop
docker-compose down
```

## 🛠️ Component Guide

### Server (`server.py`)

Central coordinator that:
- Manages work queue of Mersenne candidates
- Tracks client progress and assignments
- Stores discoveries in SQLite database
- Provides REST API for clients

**Commands**:
```bash
# Start server
python server.py --host 0.0.0.0 --port 5000

# With custom database
python server.py --db /path/to/db.db

# Debug mode
python server.py --debug
```

**API Endpoints**:
- `GET /api/health` - Server status
- `POST /api/register` - Register client
- `GET /api/assignment` - Get work assignment
- `POST /api/submit` - Submit result
- `GET /api/stats/server` - Server statistics
- `GET /api/perfects` - List perfect numbers

### Dashboard (`dashboard.py`)

Web interface showing:
- Real-time network statistics
- Active searches and progress
- Discovered perfect numbers
- User leaderboard
- Recent results

**Commands**:
```bash
# Start dashboard
python dashboard.py --host 0.0.0.0 --port 8080

# Connect to remote server
python dashboard.py --api-url http://server:5000

# Custom port
python dashboard.py --port 3000
```

**Access**: http://localhost:8080

### Client (`client.py`)

Compute node that:
- Gets assignments from server
- Runs Lucas-Lehmer primality tests
- Reports progress and results
- Supports checkpointing and resumption

**Commands**:
```bash
# Start client
python client.py --server http://localhost:5000 --username alice

# Remote server
python client.py --server https://myserver.duckdns.org --username bob

# Self-signed SSL
python client.py --server https://192.168.1.100 --username charlie --no-verify-ssl
```

**Features**:
- Fast arithmetic with gmpy2 (optional but recommended)
- Automatic progress checkpointing
- Resume interrupted tests
- Real-time progress reporting

### Admin Tool (`admin.py`)

Database management:

```bash
# Add work to queue
python admin.py add-work 521 607 1279

# Add range of primes
python admin.py add-range 10000 20000

# Show statistics
python admin.py stats

# Reset expired assignments
python admin.py reset

# Clear user assignments
python admin.py clear-user alice

# Export results
python admin.py export results.csv

# List users
python admin.py list-users
```

### Monitor (`monitor.py`)

View network status:

```bash
# Monitor local server
python monitor.py

# Monitor remote server
python monitor.py --server https://myserver.duckdns.org

# Shows:
# - Server health
# - Active assignments
# - User statistics
# - Recent discoveries
```

## 🔧 Advanced Configuration

### System Services (Linux)

Auto-start on boot:

```bash
# Install services
sudo cp perfectnet-*.service /etc/systemd/system/
sudo systemctl daemon-reload

# Enable and start
sudo systemctl enable perfectnet-server perfectnet-dashboard
sudo systemctl start perfectnet-server perfectnet-dashboard

# Check status
sudo systemctl status perfectnet-*

# View logs
sudo journalctl -u perfectnet-server -f
```

### Nginx Reverse Proxy

Production deployment with SSL:

```nginx
# /etc/nginx/sites-available/perfectnet
server {
    listen 443 ssl http2;
    server_name perfectnet.example.com;
    
    ssl_certificate /etc/letsencrypt/live/perfectnet.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/perfectnet.example.com/privkey.pem;
    
    location /api/ {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
    }
}
```

### Environment Variables

Configure via environment:

```bash
# Server
export SERVER_HOST=0.0.0.0
export SERVER_PORT=5000
export DB_PATH=/data/perfectnet.db

# Dashboard
export API_URL=http://localhost:5000
export DASHBOARD_PORT=8080

# Client
export SERVER_URL=http://localhost:5000
export USERNAME=myuser
```

### Firewall Configuration

**UFW (Ubuntu)**:
```bash
# Local network only
sudo ufw allow from 192.168.0.0/16 to any port 5000
sudo ufw allow from 192.168.0.0/16 to any port 8080

# Production with nginx
sudo ufw allow 'Nginx Full'
sudo ufw deny 5000/tcp
sudo ufw deny 8080/tcp
```

**firewalld (RHEL/CentOS)**:
```bash
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload
```

## 🐛 Troubleshooting

### Test Network Connectivity

```bash
# Run comprehensive network test
python test_network.py http://your-server:5000

# Quick test
python test_network.py --quick http://localhost:5000

# Full test with performance
python test_network.py --full https://production.com
```

### Common Issues

**Client can't connect**:
```bash
# Check server is running
curl http://localhost:5000/api/health

# Check firewall
sudo ufw status
sudo netstat -tlnp | grep 5000

# Test from client machine
telnet server-ip 5000
```

**gmpy2 won't install**:
```bash
# Install system dependencies first
sudo apt install libgmp-dev libmpfr-dev libmpc-dev gcc g++
pip install gmpy2

# Or use without gmpy2 (slower)
# The system will fall back to Python integers
```

**SSL certificate errors**:
```bash
# For self-signed certificates
python client.py --server https://server --no-verify-ssl --username alice

# Check certificate
sudo certbot certificates

# Renew certificate
sudo certbot renew
```

**Service won't start**:
```bash
# Check logs
sudo journalctl -u perfectnet-server -n 50

# Test manually
sudo -u perfectnet /opt/perfectnet/venv/bin/python /opt/perfectnet/server.py

# Check permissions
ls -la /var/lib/perfectnet
sudo chown -R perfectnet:perfectnet /var/lib/perfectnet
```

**Database locked**:
```bash
# Check for multiple instances
ps aux | grep server.py

# Kill old instances
pkill -f server.py

# Reset if needed
sudo systemctl restart perfectnet-server
```

## 📊 Performance Tips

1. **Use gmpy2** for 10-100x faster arithmetic
2. **Run multiple clients** to parallelize work
3. **Use SSD storage** for database
4. **Allocate enough RAM** (2GB+ per client)
5. **Monitor progress**: `python monitor.py`

## 🔒 Security Checklist

- [ ] Use HTTPS in production (Let's Encrypt)
- [ ] Run services as non-root user
- [ ] Use nginx reverse proxy
- [ ] Configure firewall (block direct Flask access)
- [ ] Enable rate limiting
- [ ] Regular security updates
- [ ] Monitor logs for suspicious activity
- [ ] Backup database regularly
- [ ] Use strong passwords/API keys
- [ ] Restrict SSH access (fail2ban)

## 📚 Documentation

- [DEPLOYMENT.md](DEPLOYMENT.md) - Comprehensive deployment guide
- [nginx.conf](nginx.conf) - Reverse proxy configuration
- [setup.sh](setup.sh) - Automated setup script
- [test_network.py](test_network.py) - Network diagnostics

## 🤝 Contributing

Contributions welcome! Areas for improvement:
- Additional primality tests
- PostgreSQL support
- WebSocket for real-time updates
- Distributed caching (Redis)
- Prometheus metrics
- Web-based admin panel

## 📝 License

MIT License - See LICENSE file

## 🙏 Acknowledgments

- [GIMPS](https://www.mersenne.org/) - Great Internet Mersenne Prime Search
- [GMP](https://gmplib.org/) - GNU Multiple Precision Arithmetic Library
- Euclid for the theorem (circa 300 BCE)

## 📞 Support

- GitHub Issues: https://github.com/gouthamofthenp/perfectnumbersearcher/issues
- Documentation: [DEPLOYMENT.md](DEPLOYMENT.md)
- Test connectivity: `python test_network.py <server>`

---

**Ready to discover perfect numbers?**

```bash
./setup.sh
./start.sh
python client.py --server http://localhost:5000 --username YOUR_NAME
```

Happy computing! 🎉
