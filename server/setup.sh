#!/bin/bash
# Perfect Number Network - Quick Setup Script

set -e

echo "╔═══════════════════════════════════════════════════════════╗"
echo "║  Perfect Number Network - Setup                           ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""

# Check Python version
echo "Checking Python version..."
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || { [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 8 ]; }; then
    echo "✗ Python 3.8 or higher required. Found: $PYTHON_VERSION"
    exit 1
fi

echo "✓ Python $PYTHON_VERSION found"
echo ""

# Check if virtual environment should be used
read -p "Create virtual environment? (recommended) [Y/n]: " USE_VENV
USE_VENV=${USE_VENV:-Y}

if [[ $USE_VENV =~ ^[Yy]$ ]]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    
    # Activate virtual environment
    if [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
    elif [ -f "venv/Scripts/activate" ]; then
        source venv/Scripts/activate
    else
        echo "✗ Could not find virtual environment activation script"
        exit 1
    fi
    
    echo "✓ Virtual environment created and activated"
    echo ""
fi

# Install system dependencies for gmpy2
echo "Checking system dependencies..."

if command -v apt-get &> /dev/null; then
    echo "Detected Debian/Ubuntu system"
    read -p "Install gmpy2 system dependencies? (requires sudo) [Y/n]: " INSTALL_DEPS
    INSTALL_DEPS=${INSTALL_DEPS:-Y}
    
    if [[ $INSTALL_DEPS =~ ^[Yy]$ ]]; then
        echo "Installing system dependencies..."
        sudo apt-get update
        sudo apt-get install -y libgmp-dev libmpfr-dev libmpc-dev gcc g++
        echo "✓ System dependencies installed"
    fi
elif command -v yum &> /dev/null; then
    echo "Detected Red Hat/CentOS system"
    read -p "Install gmpy2 system dependencies? (requires sudo) [Y/n]: " INSTALL_DEPS
    INSTALL_DEPS=${INSTALL_DEPS:-Y}
    
    if [[ $INSTALL_DEPS =~ ^[Yy]$ ]]; then
        echo "Installing system dependencies..."
        sudo yum install -y gmp-devel mpfr-devel libmpc-devel gcc gcc-c++
        echo "✓ System dependencies installed"
    fi
elif command -v brew &> /dev/null; then
    echo "Detected macOS with Homebrew"
    read -p "Install gmpy2 system dependencies? [Y/n]: " INSTALL_DEPS
    INSTALL_DEPS=${INSTALL_DEPS:-Y}
    
    if [[ $INSTALL_DEPS =~ ^[Yy]$ ]]; then
        echo "Installing system dependencies..."
        brew install gmp mpfr libmpc
        echo "✓ System dependencies installed"
    fi
else
    echo "⚠️  Could not detect package manager"
    echo "   gmpy2 requires: gmp, mpfr, and mpc libraries"
    echo "   System will work without gmpy2 but will be slower"
fi

echo ""

# Install Python dependencies
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "✓ Python dependencies installed"
echo ""

# Check if gmpy2 installed successfully
if python3 -c "import gmpy2" 2>/dev/null; then
    echo "✓ gmpy2 installed successfully - fast arithmetic enabled"
else
    echo "⚠️  gmpy2 not installed - will use slower Python integers"
    echo "   This is okay but computations will be slower"
fi

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "Setup complete!"
echo ""
echo "Quick Start:"
echo "  1. Start server:     python server.py --host 0.0.0.0 --port 5000"
echo "  2. Start dashboard:  python dashboard.py --host 0.0.0.0 --port 8080"
echo "  3. Start client:     python client.py --username YOUR_NAME"
echo ""
echo "For public access, see README.md for port forwarding instructions"
echo ""

read -p "Would you like to initialize the database now? [Y/n]: " INIT_DB
INIT_DB=${INIT_DB:-Y}

if [[ $INIT_DB =~ ^[Yy]$ ]]; then
    echo ""
    echo "Initializing database..."
    python3 << EOF
import sys
sys.path.insert(0, '.')
from server import init_database
init_database()
print("✓ Database initialized")
EOF
fi

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "Ready to start searching for perfect numbers!"
echo "═══════════════════════════════════════════════════════════"
