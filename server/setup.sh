#!/bin/bash
# Perfect Number Network - Universal Setup Script
# Supports: Local network, DuckDNS, AWS, Cloud hosting, etc.

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
print_header() {
    echo -e "${BLUE}╔═══════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║${NC}  $1"
    echo -e "${BLUE}╚═══════════════════════════════════════════════════════════╝${NC}"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC}  $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC}  $1"
}

# Detect environment
detect_environment() {
    if [ -f /.dockerenv ]; then
        echo "docker"
    elif [ -f /sys/hypervisor/uuid ] && grep -q ec2 /sys/hypervisor/uuid 2>/dev/null; then
        echo "aws"
    elif [ -f /sys/class/dmi/id/product_name ] && grep -qi "google" /sys/class/dmi/id/product_name 2>/dev/null; then
        echo "gcp"
    elif [ -f /sys/class/dmi/id/sys_vendor ] && grep -qi "microsoft" /sys/class/dmi/id/sys_vendor 2>/dev/null; then
        echo "azure"
    else
        echo "local"
    fi
}

# Detect package manager
detect_package_manager() {
    if command -v apt-get &> /dev/null; then
        echo "apt"
    elif command -v yum &> /dev/null; then
        echo "yum"
    elif command -v dnf &> /dev/null; then
        echo "dnf"
    elif command -v brew &> /dev/null; then
        echo "brew"
    else
        echo "unknown"
    fi
}

# Get server's public IP
get_public_ip() {
    curl -s http://checkip.amazonaws.com || \
    curl -s http://ifconfig.me || \
    curl -s http://icanhazip.com || \
    echo "unknown"
}

# Get server's local IP
get_local_ip() {
    hostname -I | awk '{print $1}' || \
    ip route get 1 | awk '{print $7;exit}' || \
    echo "unknown"
}

print_header "Perfect Number Network - Setup"
echo ""

# Detect environment
ENV=$(detect_environment)
PKG_MGR=$(detect_package_manager)
PUBLIC_IP=$(get_public_ip)
LOCAL_IP=$(get_local_ip)

print_info "Environment detected: $ENV"
print_info "Package manager: $PKG_MGR"
print_info "Public IP: $PUBLIC_IP"
print_info "Local IP: $LOCAL_IP"
echo ""

# Check Python version
print_info "Checking Python version..."
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed"
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || { [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 8 ]; }; then
    print_error "Python 3.8 or higher required. Found: $PYTHON_VERSION"
    exit 1
fi

print_success "Python $PYTHON_VERSION found"
echo ""

# Ask for deployment type
print_header "Deployment Configuration"
echo ""
echo "Select your deployment type:"
echo "  1) Local network only (HTTP, no SSL)"
echo "  2) Local network with self-signed SSL"
echo "  3) Public server with domain (Let's Encrypt SSL)"
echo "  4) Public server with DuckDNS (Let's Encrypt SSL)"
echo "  5) Cloud provider (AWS/GCP/Azure with domain)"
echo "  6) Development only (no reverse proxy)"
echo ""
read -p "Enter choice [1-6]: " DEPLOY_TYPE
DEPLOY_TYPE=${DEPLOY_TYPE:-6}

# Get installation directory
INSTALL_DIR=$(pwd)
echo ""
read -p "Installation directory [$INSTALL_DIR]: " USER_INSTALL_DIR
INSTALL_DIR=${USER_INSTALL_DIR:-$INSTALL_DIR}

# Create virtual environment
echo ""
print_info "Creating virtual environment..."
read -p "Use virtual environment? (recommended) [Y/n]: " USE_VENV
USE_VENV=${USE_VENV:-Y}

if [[ $USE_VENV =~ ^[Yy]$ ]]; then
    if [ ! -d "venv" ]; then
        python3 -m venv venv
        print_success "Virtual environment created"
    else
        print_info "Virtual environment already exists"
    fi
    
    # Activate virtual environment
    if [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
    elif [ -f "venv/Scripts/activate" ]; then
        source venv/Scripts/activate
    else
        print_error "Could not find virtual environment activation script"
        exit 1
    fi
    
    print_success "Virtual environment activated"
else
    print_warning "Skipping virtual environment (not recommended for production)"
fi
echo ""

# Install system dependencies for gmpy2
print_header "System Dependencies"
echo ""
print_info "Installing system dependencies for gmpy2 (for fast arithmetic)..."

INSTALL_DEPS="n"
if [ "$PKG_MGR" = "apt" ]; then
    print_info "Detected Debian/Ubuntu system"
    read -p "Install gmpy2 dependencies (libgmp, libmpfr, libmpc)? [Y/n]: " INSTALL_DEPS
    INSTALL_DEPS=${INSTALL_DEPS:-Y}
    
    if [[ $INSTALL_DEPS =~ ^[Yy]$ ]]; then
        sudo apt-get update
        sudo apt-get install -y libgmp-dev libmpfr-dev libmpc-dev gcc g++ build-essential
        print_success "System dependencies installed"
    fi
elif [ "$PKG_MGR" = "yum" ] || [ "$PKG_MGR" = "dnf" ]; then
    print_info "Detected Red Hat/CentOS/Fedora system"
    read -p "Install gmpy2 dependencies? [Y/n]: " INSTALL_DEPS
    INSTALL_DEPS=${INSTALL_DEPS:-Y}
    
    if [[ $INSTALL_DEPS =~ ^[Yy]$ ]]; then
        sudo $PKG_MGR install -y gmp-devel mpfr-devel libmpc-devel gcc gcc-c++
        print_success "System dependencies installed"
    fi
elif [ "$PKG_MGR" = "brew" ]; then
    print_info "Detected macOS with Homebrew"
    read -p "Install gmpy2 dependencies? [Y/n]: " INSTALL_DEPS
    INSTALL_DEPS=${INSTALL_DEPS:-Y}
    
    if [[ $INSTALL_DEPS =~ ^[Yy]$ ]]; then
        brew install gmp mpfr libmpc
        print_success "System dependencies installed"
    fi
else
    print_warning "Could not detect package manager"
    print_info "gmpy2 requires: gmp, mpfr, and mpc libraries"
    print_info "System will work without gmpy2 but will be slower"
fi
echo ""

# Install Python dependencies
print_header "Python Dependencies"
echo ""
print_info "Installing Python packages..."
pip install --upgrade pip

# Create requirements.txt if it doesn't exist
if [ ! -f "requirements.txt" ]; then
    cat > requirements.txt << EOF
flask>=2.3.0
flask-cors>=4.0.0
requests>=2.31.0
gmpy2>=2.1.5
EOF
fi

pip install -r requirements.txt
print_success "Python dependencies installed"

# Check if gmpy2 installed successfully
if python3 -c "import gmpy2" 2>/dev/null; then
    print_success "gmpy2 installed - fast arithmetic enabled"
else
    print_warning "gmpy2 not installed - will use slower Python integers"
fi
echo ""

# Initialize database
print_header "Database Setup"
echo ""
read -p "Initialize database now? [Y/n]: " INIT_DB
INIT_DB=${INIT_DB:-Y}

if [[ $INIT_DB =~ ^[Yy]$ ]]; then
    print_info "Initializing database..."
    python3 << EOF
import sys
sys.path.insert(0, '.')
from server import init_database
init_database()
print("Database initialized successfully")
EOF
    print_success "Database initialized"
fi
echo ""

# Configure for deployment type
print_header "Deployment Configuration"
echo ""

case $DEPLOY_TYPE in
    1|2)
        # Local network
        print_info "Configuring for local network access..."
        SERVER_HOST="0.0.0.0"
        SERVER_PORT="5000"
        DASHBOARD_PORT="8080"
        USE_NGINX="n"
        
        if [ "$DEPLOY_TYPE" = "2" ]; then
            print_info "Self-signed SSL will require nginx setup"
            read -p "Install and configure nginx with self-signed cert? [y/N]: " USE_NGINX
        fi
        
        echo ""
        print_info "Access URLs:"
        print_info "  Dashboard: http://$LOCAL_IP:$DASHBOARD_PORT"
        print_info "  API: http://$LOCAL_IP:$SERVER_PORT/api/health"
        print_info "  Clients use: --server http://$LOCAL_IP:$SERVER_PORT"
        ;;
        
    3|4|5)
        # Public server
        print_info "Configuring for public access..."
        SERVER_HOST="127.0.0.1"  # Behind nginx
        SERVER_PORT="5000"
        DASHBOARD_PORT="8080"
        USE_NGINX="Y"
        
        # Get domain or DuckDNS hostname
        if [ "$DEPLOY_TYPE" = "4" ]; then
            echo ""
            print_info "DuckDNS Setup:"
            print_info "1. Create account at https://www.duckdns.org"
            print_info "2. Create a subdomain (e.g., myserver.duckdns.org)"
            print_info "3. Set up DuckDNS updater with your token"
            echo ""
            read -p "Enter your DuckDNS hostname (e.g., myserver.duckdns.org): " DOMAIN
        else
            echo ""
            read -p "Enter your domain name (e.g., perfectnet.example.com): " DOMAIN
        fi
        
        if [ -z "$DOMAIN" ]; then
            print_error "Domain name is required for public setup"
            exit 1
        fi
        
        echo ""
        print_info "Domain: $DOMAIN"
        print_info "After setup, access at: https://$DOMAIN"
        ;;
        
    6)
        # Development only
        print_info "Development mode - no reverse proxy"
        SERVER_HOST="127.0.0.1"
        SERVER_PORT="5000"
        DASHBOARD_PORT="8080"
        USE_NGINX="n"
        
        echo ""
        print_info "Access URLs:"
        print_info "  Dashboard: http://localhost:$DASHBOARD_PORT"
        print_info "  API: http://localhost:$SERVER_PORT/api/health"
        ;;
esac
echo ""

# Nginx setup
if [[ $USE_NGINX =~ ^[Yy]$ ]]; then
    print_header "Nginx Setup"
    echo ""
    
    # Check if nginx is installed
    if ! command -v nginx &> /dev/null; then
        print_info "Nginx not found. Installing..."
        if [ "$PKG_MGR" = "apt" ]; then
            sudo apt-get update
            sudo apt-get install -y nginx
        elif [ "$PKG_MGR" = "yum" ] || [ "$PKG_MGR" = "dnf" ]; then
            sudo $PKG_MGR install -y nginx
        fi
        print_success "Nginx installed"
    fi
    
    # Copy nginx config
    if [ -f "nginx.conf" ]; then
        print_info "Installing nginx configuration..."
        sudo cp nginx.conf /etc/nginx/sites-available/perfectnet 2>/dev/null || \
        sudo cp nginx.conf /etc/nginx/conf.d/perfectnet.conf
        
        # Update server_name if domain provided
        if [ ! -z "$DOMAIN" ]; then
            if [ -f /etc/nginx/sites-available/perfectnet ]; then
                sudo sed -i "s/perfectnet.example.com/$DOMAIN/g" /etc/nginx/sites-available/perfectnet
                sudo ln -sf /etc/nginx/sites-available/perfectnet /etc/nginx/sites-enabled/ 2>/dev/null || true
            else
                sudo sed -i "s/perfectnet.example.com/$DOMAIN/g" /etc/nginx/conf.d/perfectnet.conf
            fi
        fi
        
        # Test nginx config
        if sudo nginx -t 2>/dev/null; then
            print_success "Nginx configuration valid"
            sudo systemctl reload nginx 2>/dev/null || true
        else
            print_warning "Nginx configuration needs manual adjustment"
        fi
    fi
    
    # SSL setup
    if [ "$DEPLOY_TYPE" -ge 3 ] && [ "$DEPLOY_TYPE" -le 5 ]; then
        echo ""
        print_info "SSL Certificate Setup:"
        print_info "Install Let's Encrypt certificate with:"
        echo ""
        echo "  sudo apt install certbot python3-certbot-nginx  # Ubuntu/Debian"
        echo "  sudo yum install certbot python3-certbot-nginx  # RHEL/CentOS"
        echo ""
        echo "  sudo certbot --nginx -d $DOMAIN"
        echo ""
    fi
fi

# Systemd service setup
print_header "System Service Setup"
echo ""
read -p "Install as systemd services (auto-start on boot)? [y/N]: " INSTALL_SERVICE
INSTALL_SERVICE=${INSTALL_SERVICE:-n}

if [[ $INSTALL_SERVICE =~ ^[Yy]$ ]]; then
    print_info "Installing systemd services..."
    
    # Create perfectnet user if needed
    if ! id "perfectnet" &>/dev/null; then
        sudo useradd -r -s /bin/false perfectnet
        print_success "Created perfectnet user"
    fi
    
    # Set up directories
    sudo mkdir -p /var/lib/perfectnet
    sudo chown perfectnet:perfectnet /var/lib/perfectnet
    
    # Create service files with correct paths
    cat > /tmp/perfectnet-server.service << EOF
[Unit]
Description=Perfect Number Network Server
After=network.target
Documentation=https://github.com/yourrepo/perfectnet

[Service]
Type=simple
User=perfectnet
Group=perfectnet
WorkingDirectory=$INSTALL_DIR
Environment="PATH=$INSTALL_DIR/venv/bin:/usr/local/bin:/usr/bin:/bin"

ExecStart=$INSTALL_DIR/venv/bin/python $INSTALL_DIR/server.py --host $SERVER_HOST --port $SERVER_PORT --db /var/lib/perfectnet/perfectnet.db

Restart=always
RestartSec=10
StartLimitInterval=0

LimitNOFILE=65536
MemoryLimit=2G

NoNewPrivileges=true
PrivateTmp=true

StandardOutput=journal
StandardError=journal
SyslogIdentifier=perfectnet-server

[Install]
WantedBy=multi-user.target
EOF

    cat > /tmp/perfectnet-dashboard.service << EOF
[Unit]
Description=Perfect Number Network Dashboard
After=network.target perfectnet-server.service
Requires=perfectnet-server.service
Documentation=https://github.com/yourrepo/perfectnet

[Service]
Type=simple
User=perfectnet
Group=perfectnet
WorkingDirectory=$INSTALL_DIR
Environment="PATH=$INSTALL_DIR/venv/bin:/usr/local/bin:/usr/bin:/bin"

ExecStart=$INSTALL_DIR/venv/bin/python $INSTALL_DIR/dashboard.py --host $SERVER_HOST --port $DASHBOARD_PORT --api-url http://127.0.0.1:$SERVER_PORT

Restart=always
RestartSec=10
StartLimitInterval=0

LimitNOFILE=4096
MemoryLimit=512M

NoNewPrivileges=true
PrivateTmp=true

StandardOutput=journal
StandardError=journal
SyslogIdentifier=perfectnet-dashboard

[Install]
WantedBy=multi-user.target
EOF

    sudo mv /tmp/perfectnet-server.service /etc/systemd/system/
    sudo mv /tmp/perfectnet-dashboard.service /etc/systemd/system/
    
    # Fix permissions
    sudo chown -R perfectnet:perfectnet $INSTALL_DIR 2>/dev/null || true
    
    sudo systemctl daemon-reload
    sudo systemctl enable perfectnet-server perfectnet-dashboard
    
    print_success "Systemd services installed"
    echo ""
    print_info "Service management commands:"
    echo "  sudo systemctl start perfectnet-server"
    echo "  sudo systemctl start perfectnet-dashboard"
    echo "  sudo systemctl status perfectnet-server"
    echo "  sudo systemctl status perfectnet-dashboard"
    echo "  sudo journalctl -u perfectnet-server -f"
fi
echo ""

# Firewall configuration
print_header "Firewall Configuration"
echo ""

if command -v ufw &> /dev/null; then
    print_info "Detected UFW firewall"
    read -p "Configure UFW firewall? [y/N]: " CONFIG_FW
    
    if [[ $CONFIG_FW =~ ^[Yy]$ ]]; then
        if [[ $USE_NGINX =~ ^[Yy]$ ]]; then
            sudo ufw allow 'Nginx Full'
            sudo ufw deny 5000/tcp
            sudo ufw deny 8080/tcp
        else
            sudo ufw allow $SERVER_PORT/tcp
            sudo ufw allow $DASHBOARD_PORT/tcp
        fi
        print_success "Firewall configured"
    fi
elif command -v firewall-cmd &> /dev/null; then
    print_info "Detected firewalld"
    read -p "Configure firewalld? [y/N]: " CONFIG_FW
    
    if [[ $CONFIG_FW =~ ^[Yy]$ ]]; then
        if [[ $USE_NGINX =~ ^[Yy]$ ]]; then
            sudo firewall-cmd --permanent --add-service=http
            sudo firewall-cmd --permanent --add-service=https
            sudo firewall-cmd --permanent --remove-port=5000/tcp 2>/dev/null || true
            sudo firewall-cmd --permanent --remove-port=8080/tcp 2>/dev/null || true
        else
            sudo firewall-cmd --permanent --add-port=$SERVER_PORT/tcp
            sudo firewall-cmd --permanent --add-port=$DASHBOARD_PORT/tcp
        fi
        sudo firewall-cmd --reload
        print_success "Firewall configured"
    fi
elif [ "$ENV" = "aws" ]; then
    print_info "AWS environment detected"
    print_warning "Configure AWS Security Group:"
    if [[ $USE_NGINX =~ ^[Yy]$ ]]; then
        print_info "  - Allow inbound: 80/tcp, 443/tcp from 0.0.0.0/0"
        print_info "  - Block: 5000/tcp, 8080/tcp"
    else
        print_info "  - Allow inbound: $SERVER_PORT/tcp, $DASHBOARD_PORT/tcp from 0.0.0.0/0"
    fi
else
    print_info "No firewall detected or manual configuration required"
fi
echo ""

# Create startup script
cat > start.sh << EOF
#!/bin/bash
# Perfect Number Network - Quick Start Script

cd $INSTALL_DIR

# Activate virtual environment
if [ -f venv/bin/activate ]; then
    source venv/bin/activate
fi

# Start server in background
echo "Starting server..."
python server.py --host $SERVER_HOST --port $SERVER_PORT &
SERVER_PID=\$!

# Wait for server to start
sleep 3

# Start dashboard in background
echo "Starting dashboard..."
python dashboard.py --host $SERVER_HOST --port $DASHBOARD_PORT --api-url http://127.0.0.1:$SERVER_PORT &
DASHBOARD_PID=\$!

echo ""
echo "Perfect Number Network is running!"
echo ""
EOF

if [[ $USE_NGINX =~ ^[Yy]$ ]] && [ ! -z "$DOMAIN" ]; then
    cat >> start.sh << EOF
echo "Dashboard: https://$DOMAIN"
echo "API: https://$DOMAIN/api/health"
echo ""
echo "Client command:"
echo "  python client.py --server https://$DOMAIN --username YOUR_NAME"
EOF
else
    cat >> start.sh << EOF
echo "Dashboard: http://$LOCAL_IP:$DASHBOARD_PORT"
echo "API: http://$LOCAL_IP:$SERVER_PORT/api/health"
echo ""
echo "Client command:"
echo "  python client.py --server http://$LOCAL_IP:$SERVER_PORT --username YOUR_NAME"
EOF
fi

cat >> start.sh << EOF
echo ""
echo "Press Ctrl+C to stop both services"
echo ""

# Wait for interrupt
trap "kill \$SERVER_PID \$DASHBOARD_PID 2>/dev/null; exit 0" INT TERM
wait
EOF

chmod +x start.sh
print_success "Created start.sh script"
echo ""

# Final summary
print_header "Setup Complete!"
echo ""

case $DEPLOY_TYPE in
    1|2|6)
        print_success "Local/Development Setup Complete"
        echo ""
        print_info "Quick Start:"
        echo "  ./start.sh"
        echo ""
        print_info "Or manually:"
        echo "  python server.py --host $SERVER_HOST --port $SERVER_PORT"
        echo "  python dashboard.py --host $SERVER_HOST --port $DASHBOARD_PORT"
        echo "  python client.py --server http://$LOCAL_IP:$SERVER_PORT --username YOUR_NAME"
        echo ""
        print_info "Access dashboard at: http://$LOCAL_IP:$DASHBOARD_PORT"
        ;;
    3|4|5)
        print_success "Public Server Setup Complete"
        echo ""
        print_info "Next steps:"
        echo "  1. Start services:"
        if [[ $INSTALL_SERVICE =~ ^[Yy]$ ]]; then
            echo "     sudo systemctl start perfectnet-server perfectnet-dashboard"
        else
            echo "     ./start.sh"
        fi
        echo ""
        echo "  2. Configure DNS:"
        if [ "$DEPLOY_TYPE" = "4" ]; then
            echo "     - Set up DuckDNS updater"
            echo "     - Wait for DNS propagation"
        else
            echo "     - Point $DOMAIN to $PUBLIC_IP"
            echo "     - Wait for DNS propagation"
        fi
        echo ""
        echo "  3. Get SSL certificate:"
        echo "     sudo certbot --nginx -d $DOMAIN"
        echo ""
        print_info "After DNS + SSL setup:"
        echo "  Dashboard: https://$DOMAIN"
        echo "  Client: python client.py --server https://$DOMAIN --username YOUR_NAME"
        ;;
esac

echo ""
print_info "Documentation:"
echo "  - Admin commands: python admin.py --help"
echo "  - Monitor status: python monitor.py --server YOUR_SERVER"
echo "  - View logs: sudo journalctl -u perfectnet-server -f"
echo ""

if [ "$ENV" = "aws" ] || [ "$ENV" = "gcp" ] || [ "$ENV" = "azure" ]; then
    print_warning "Cloud Environment Checklist:"
    echo "  - Security group/firewall rules configured"
    echo "  - DNS A record points to $PUBLIC_IP"
    echo "  - SSL certificate obtained"
    echo "  - Services are running"
fi

echo ""
print_success "Ready to start searching for perfect numbers!"
echo ""
