# Perfect Number Network - Deployment Guide

Complete guide for deploying Perfect Number Network in various scenarios: local network, DuckDNS, cloud providers, and more.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Setup](#quick-setup)
3. [Deployment Scenarios](#deployment-scenarios)
   - [Local Development](#scenario-1-local-development)
   - [Local Network](#scenario-2-local-network-http)
   - [Local Network with SSL](#scenario-3-local-network-with-ssl)
   - [DuckDNS Setup](#scenario-4-duckdns-dynamic-dns)
   - [Cloud with Domain](#scenario-5-cloud-with-domain-aws-gcp-azure)
   - [Behind Load Balancer](#scenario-6-behind-load-balancer)
4. [Troubleshooting](#troubleshooting)
5. [Security Best Practices](#security-best-practices)

---

## Prerequisites

### System Requirements

- **OS**: Linux (Ubuntu/Debian/RHEL/CentOS), macOS, or Windows WSL2
- **Python**: 3.8 or higher
- **RAM**: 2GB minimum, 4GB recommended
- **Disk**: 1GB minimum
- **Network**: Internet connection for package installation

### Required Software

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3 python3-pip python3-venv git

# RHEL/CentOS
sudo yum install python3 python3-pip git

# macOS
brew install python3
```

### Optional (for fast arithmetic)

```bash
# Ubuntu/Debian
sudo apt install libgmp-dev libmpfr-dev libmpc-dev gcc g++

# RHEL/CentOS
sudo yum install gmp-devel mpfr-devel libmpc-devel gcc gcc-c++

# macOS
brew install gmp mpfr libmpc
```

---

## Quick Setup

### Automated Setup

```bash
# Clone or download the project
cd perfectnet

# Run setup script
chmod +x setup.sh
./setup.sh

# Follow the prompts to select your deployment type
```

### Manual Setup

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install flask flask-cors requests gmpy2

# Initialize database
python3 -c "from server import init_database; init_database()"
```

---

## Deployment Scenarios

### Scenario 1: Local Development

**Use Case**: Testing and development on your local machine

**Setup**:

```bash
# Terminal 1: Start server
python server.py --host 127.0.0.1 --port 5000

# Terminal 2: Start dashboard
python dashboard.py --host 127.0.0.1 --port 8080

# Terminal 3: Start client
python client.py --server http://localhost:5000 --username dev_user
```

**Access**:
- Dashboard: http://localhost:8080
- API: http://localhost:5000/api/health

**Configuration**:
- No firewall configuration needed
- No SSL required
- No nginx needed
- Files stored locally

---

### Scenario 2: Local Network (HTTP)

**Use Case**: Access from other devices on your home/office network

**Setup**:

```bash
# Get your local IP
ip addr show | grep "inet " | grep -v 127.0.0.1

# Example output: 192.168.1.100

# Start server (listen on all interfaces)
python server.py --host 0.0.0.0 --port 5000

# Start dashboard
python dashboard.py --host 0.0.0.0 --port 8080 --api-url http://192.168.1.100:5000
```

**Firewall Configuration**:

```bash
# Ubuntu/Debian with UFW
sudo ufw allow from 192.168.0.0/16 to any port 5000
sudo ufw allow from 192.168.0.0/16 to any port 8080

# RHEL/CentOS with firewalld
sudo firewall-cmd --permanent --add-rich-rule='rule family="ipv4" source address="192.168.0.0/16" port port="5000" protocol="tcp" accept'
sudo firewall-cmd --permanent --add-rich-rule='rule family="ipv4" source address="192.168.0.0/16" port port="8080" protocol="tcp" accept'
sudo firewall-cmd --reload
```

**Access from other devices**:

```bash
# Dashboard
http://192.168.1.100:8080

# Client
python client.py --server http://192.168.1.100:5000 --username alice
```

**Router Configuration** (optional - for internet access):
1. Find your router's admin page (usually 192.168.1.1 or 192.168.0.1)
2. Set up port forwarding:
   - External Port 5000 → Internal IP 192.168.1.100 Port 5000
   - External Port 8080 → Internal IP 192.168.1.100 Port 8080
3. Access via your public IP (find it at http://whatismyip.com)

---

### Scenario 3: Local Network with SSL

**Use Case**: Secure access on local network with self-signed certificate

**Generate Self-Signed Certificate**:

```bash
# Create certificate directory
sudo mkdir -p /etc/ssl/perfectnet

# Generate certificate (valid for 1 year)
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /etc/ssl/perfectnet/private.key \
  -out /etc/ssl/perfectnet/certificate.crt \
  -subj "/C=US/ST=State/L=City/O=Organization/CN=192.168.1.100"

# Set permissions
sudo chmod 600 /etc/ssl/perfectnet/private.key
sudo chmod 644 /etc/ssl/perfectnet/certificate.crt
```

**Install and Configure Nginx**:

```bash
# Install nginx
sudo apt install nginx  # Ubuntu/Debian
sudo yum install nginx  # RHEL/CentOS

# Copy configuration
sudo cp nginx.conf /etc/nginx/sites-available/perfectnet

# Edit the configuration
sudo nano /etc/nginx/sites-available/perfectnet

# Update these lines:
#   server_name 192.168.1.100;  # Your local IP
#   ssl_certificate /etc/ssl/perfectnet/certificate.crt;
#   ssl_certificate_key /etc/ssl/perfectnet/private.key;

# Enable site
sudo ln -s /etc/nginx/sites-available/perfectnet /etc/nginx/sites-enabled/

# Test configuration
sudo nginx -t

# Start nginx
sudo systemctl enable nginx
sudo systemctl start nginx
```

**Start Services** (behind nginx):

```bash
# Server listens on localhost only
python server.py --host 127.0.0.1 --port 5000

# Dashboard listens on localhost only
python dashboard.py --host 127.0.0.1 --port 8080 --api-url http://127.0.0.1:5000
```

**Access**:
- Dashboard: https://192.168.1.100
- Note: Browser will warn about self-signed certificate - this is normal

**Client Usage**:

```bash
# Client needs to ignore SSL warnings
python client.py --server https://192.168.1.100 --username alice --no-verify-ssl
```

---

### Scenario 4: DuckDNS Dynamic DNS

**Use Case**: Public access via DuckDNS hostname with Let's Encrypt SSL

**Step 1: Set up DuckDNS**

1. Go to https://www.duckdns.org
2. Sign in (GitHub, Google, etc.)
3. Create a subdomain (e.g., `myserver.duckdns.org`)
4. Note your token

**Step 2: Install DuckDNS Updater**

```bash
# Create directory
mkdir -p ~/duckdns
cd ~/duckdns

# Create update script
cat > duck.sh << 'EOF'
#!/bin/bash
echo url="https://www.duckdns.org/update?domains=YOUR_SUBDOMAIN&token=YOUR_TOKEN&ip=" | curl -k -o ~/duckdns/duck.log -K -
EOF

# Replace YOUR_SUBDOMAIN and YOUR_TOKEN
nano duck.sh

# Make executable
chmod +x duck.sh

# Test it
./duck.sh
cat duck.log  # Should show "OK"

# Set up cron job (update every 5 minutes)
crontab -e
# Add this line:
# */5 * * * * ~/duckdns/duck.sh >/dev/null 2>&1
```

**Step 3: Configure Router Port Forwarding**

1. Access router admin page
2. Forward ports to your server:
   - Port 80 (HTTP) → 192.168.1.100:80
   - Port 443 (HTTPS) → 192.168.1.100:443

**Step 4: Install Nginx and Certbot**

```bash
# Install packages
sudo apt install nginx certbot python3-certbot-nginx

# Copy nginx configuration
sudo cp nginx.conf /etc/nginx/sites-available/perfectnet

# Edit configuration
sudo nano /etc/nginx/sites-available/perfectnet
# Change server_name to: myserver.duckdns.org

# Enable site
sudo ln -s /etc/nginx/sites-available/perfectnet /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

**Step 5: Get Let's Encrypt Certificate**

```bash
# Get certificate
sudo certbot --nginx -d myserver.duckdns.org

# Follow the prompts:
# - Enter email address
# - Agree to terms
# - Choose to redirect HTTP to HTTPS (recommended)

# Test auto-renewal
sudo certbot renew --dry-run
```

**Step 6: Start Services**

```bash
# Install as systemd services
sudo cp perfectnet-server.service /etc/systemd/system/
sudo cp perfectnet-dashboard.service /etc/systemd/system/

# Edit service files to update paths
sudo nano /etc/systemd/system/perfectnet-server.service
sudo nano /etc/systemd/system/perfectnet-dashboard.service

# Update ExecStart in dashboard service:
# --api-url https://myserver.duckdns.org

# Start services
sudo systemctl daemon-reload
sudo systemctl enable perfectnet-server perfectnet-dashboard
sudo systemctl start perfectnet-server perfectnet-dashboard

# Check status
sudo systemctl status perfectnet-server perfectnet-dashboard
```

**Access**:
- Dashboard: https://myserver.duckdns.org
- API: https://myserver.duckdns.org/api/health

**Client Usage**:

```bash
python client.py --server https://myserver.duckdns.org --username alice
```

---

### Scenario 5: Cloud with Domain (AWS/GCP/Azure)

**Use Case**: Production deployment on cloud provider with custom domain

#### AWS EC2 Example

**Step 1: Launch EC2 Instance**

1. Launch Ubuntu 22.04 LTS instance (t2.small or larger)
2. Configure Security Group:
   - Port 22 (SSH) from your IP
   - Port 80 (HTTP) from anywhere (0.0.0.0/0)
   - Port 443 (HTTPS) from anywhere (0.0.0.0/0)
3. Allocate Elastic IP and associate with instance
4. SSH into instance

**Step 2: Configure DNS**

1. In Route 53 (or your DNS provider):
   - Create A record: `perfectnet.example.com` → Elastic IP
   - Wait for DNS propagation (use `nslookup perfectnet.example.com`)

**Step 3: Install Software**

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y python3 python3-pip python3-venv nginx certbot python3-certbot-nginx git
sudo apt install -y libgmp-dev libmpfr-dev libmpc-dev gcc g++

# Create user
sudo useradd -r -s /bin/false perfectnet
sudo mkdir -p /opt/perfectnet /var/lib/perfectnet
sudo chown perfectnet:perfectnet /var/lib/perfectnet
```

**Step 4: Deploy Application**

```bash
# Clone/upload your code
cd /opt/perfectnet
# Upload your files here

# Set up virtual environment
sudo python3 -m venv venv
sudo venv/bin/pip install flask flask-cors requests gmpy2

# Initialize database
sudo -u perfectnet venv/bin/python server.py --host 127.0.0.1 --port 5000 &
sleep 5
sudo -u perfectnet venv/bin/python -c "from server import init_database; init_database()"
# Stop the server (Ctrl+C)

# Set permissions
sudo chown -R perfectnet:perfectnet /opt/perfectnet
```

**Step 5: Configure Nginx**

```bash
# Copy configuration
sudo cp nginx.conf /etc/nginx/sites-available/perfectnet

# Edit configuration
sudo nano /etc/nginx/sites-available/perfectnet
# Update server_name: perfectnet.example.com

# Enable site
sudo ln -s /etc/nginx/sites-available/perfectnet /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

**Step 6: Get SSL Certificate**

```bash
sudo certbot --nginx -d perfectnet.example.com
```

**Step 7: Install Systemd Services**

```bash
# Copy and configure service files
sudo cp perfectnet-server.service /etc/systemd/system/
sudo cp perfectnet-dashboard.service /etc/systemd/system/

# Edit services
sudo nano /etc/systemd/system/perfectnet-server.service
# Update WorkingDirectory=/opt/perfectnet
# Update ExecStart paths

sudo nano /etc/systemd/system/perfectnet-dashboard.service
# Update WorkingDirectory=/opt/perfectnet
# Update --api-url https://perfectnet.example.com

# Start services
sudo systemctl daemon-reload
sudo systemctl enable perfectnet-server perfectnet-dashboard
sudo systemctl start perfectnet-server perfectnet-dashboard
```

**Step 8: Verify**

```bash
# Check services
sudo systemctl status perfectnet-server perfectnet-dashboard

# Test endpoints
curl https://perfectnet.example.com/api/health
curl https://perfectnet.example.com/health
```

#### GCP Compute Engine / Azure VM

Similar process to AWS, with platform-specific differences:

**GCP**:
- Use Cloud DNS for domain management
- Configure VPC firewall rules instead of Security Groups
- Use Cloud Load Balancer for multiple instances (optional)

**Azure**:
- Use Azure DNS or external DNS provider
- Configure Network Security Groups
- Use Azure Load Balancer or Application Gateway (optional)

---

### Scenario 6: Behind Load Balancer

**Use Case**: High availability with multiple backend servers

**Architecture**:
```
                          ┌─────────────┐
                          │Load Balancer│
                          │  (Nginx)    │
                          └──────┬──────┘
                                 │
                 ┌───────────────┼───────────────┐
                 │               │               │
            ┌────▼────┐     ┌────▼────┐     ┌────▼────┐
            │Server 1 │     │Server 2 │     │Server 3 │
            │API:5000 │     │API:5000 │     │API:5000 │
            │Dash:8080│     │Dash:8080│     │Dash:8080│
            └─────────┘     └─────────┘     └─────────┘
                                 │
                          ┌──────▼──────┐
                          │  Database   │
                          │  (Shared)   │
                          └─────────────┘
```

**Load Balancer Configuration** (nginx.conf on LB):

```nginx
upstream perfectnet_api {
    least_conn;
    server 192.168.1.101:5000 max_fails=3 fail_timeout=30s;
    server 192.168.1.102:5000 max_fails=3 fail_timeout=30s;
    server 192.168.1.103:5000 max_fails=3 fail_timeout=30s;
}

upstream perfectnet_dashboard {
    least_conn;
    server 192.168.1.101:8080 max_fails=3 fail_timeout=30s;
    server 192.168.1.102:8080 max_fails=3 fail_timeout=30s;
    server 192.168.1.103:8080 max_fails=3 fail_timeout=30s;
}

server {
    listen 80;
    server_name perfectnet.example.com;
    
    location /api/ {
        proxy_pass http://perfectnet_api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
    
    location / {
        proxy_pass http://perfectnet_dashboard;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

**Shared Database Setup**:

All servers point to the same database file:

```bash
# On each server, update ExecStart in service file:
--db /shared/network/path/perfectnet.db

# Or use NFS/shared storage
```

**Health Checks**:

Load balancer monitors `/api/health` and `/health` endpoints.

---

## Troubleshooting

### Connection Issues

**Problem**: Client can't connect to server

```bash
# Diagnose connection
python network_utils.py http://your-server:5000

# Check if port is open
telnet your-server 5000

# Test API directly
curl http://your-server:5000/api/health
```

**Solutions**:
1. Verify server is running: `sudo systemctl status perfectnet-server`
2. Check firewall: `sudo ufw status` or `sudo firewall-cmd --list-all`
3. Verify correct port and IP
4. Check logs: `sudo journalctl -u perfectnet-server -n 50`

### SSL Certificate Issues

**Problem**: SSL certificate errors

```bash
# Check certificate
sudo certbot certificates

# Renew certificate
sudo certbot renew

# Test renewal
sudo certbot renew --dry-run
```

**For self-signed certificates**:
```bash
# Client side
python client.py --server https://server --username alice --no-verify-ssl
```

### Service Won't Start

```bash
# Check service status
sudo systemctl status perfectnet-server

# View detailed logs
sudo journalctl -u perfectnet-server -n 100 --no-pager

# Test manually
sudo -u perfectnet /opt/perfectnet/venv/bin/python /opt/perfectnet/server.py

# Check permissions
ls -la /opt/perfectnet
ls -la /var/lib/perfectnet
```

### Port Already in Use

```bash
# Find what's using the port
sudo netstat -tlnp | grep 5000

# Kill the process
sudo kill <PID>

# Or use a different port
```

### Database Issues

```bash
# Reset database
sudo systemctl stop perfectnet-server
sudo rm /var/lib/perfectnet/perfectnet.db
sudo -u perfectnet /opt/perfectnet/venv/bin/python -c "from server import init_database; init_database()"
sudo systemctl start perfectnet-server
```

### Dashboard Not Updating

1. Check API connection in browser console (F12)
2. Verify API URL in dashboard service
3. Check CORS headers: `curl -I http://server:5000/api/health`
4. Clear browser cache

---

## Security Best Practices

### Production Checklist

- [ ] Use HTTPS (Let's Encrypt or commercial certificate)
- [ ] Run services as dedicated user (not root)
- [ ] Use nginx reverse proxy (don't expose Flask directly)
- [ ] Configure firewall (block direct Flask access)
- [ ] Enable rate limiting in nginx
- [ ] Use strong API keys
- [ ] Regular security updates: `sudo apt update && sudo apt upgrade`
- [ ] Monitor logs: `sudo journalctl -u perfectnet-* -f`
- [ ] Set up automatic backups
- [ ] Use fail2ban for SSH protection
- [ ] Restrict database file permissions

### Firewall Rules

```bash
# Production (with nginx)
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'
sudo ufw deny 5000/tcp
sudo ufw deny 8080/tcp
sudo ufw enable
```

### Regular Maintenance

```bash
# Update system
sudo apt update && sudo apt upgrade

# Renew SSL certificates (automatic, but verify)
sudo certbot renew --dry-run

# Rotate logs
sudo journalctl --vacuum-time=30d

# Backup database
sudo cp /var/lib/perfectnet/perfectnet.db /backup/location/
```

---

## Additional Resources

- [nginx Documentation](https://nginx.org/en/docs/)
- [Let's Encrypt](https://letsencrypt.org/)
- [DuckDNS](https://www.duckdns.org/)
- [Flask Deployment](https://flask.palletsprojects.com/en/2.3.x/deploying/)
- [systemd Documentation](https://www.freedesktop.org/software/systemd/man/systemd.service.html)

---

## Support

For issues or questions:
1. Check logs: `sudo journalctl -u perfectnet-server -n 100`
2. Run diagnostics: `python network_utils.py http://your-server:5000`
3. Review this guide
4. Check firewall and network configuration
