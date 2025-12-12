#!/bin/bash
# First-time setup script for Ubuntu servers
# Run this once before starting the application

echo "========================================"
echo "  Log Analytics - Setup"
echo "========================================"
echo ""

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    echo "WARNING: Running as root. Consider using a regular user."
    echo ""
fi

# Update package list
echo "[1/5] Updating package list..."
sudo apt-get update -qq

# Install Python 3 if not present
echo ""
echo "[2/5] Installing Python 3..."
if ! command -v python3 &> /dev/null; then
    sudo apt-get install -y python3 python3-pip python3-venv
    echo "Python 3 installed"
else
    echo "Python 3 already installed: $(python3 --version)"
fi

# Install pip if not present
if ! command -v pip3 &> /dev/null; then
    echo "Installing pip..."
    sudo apt-get install -y python3-pip
fi

# Install required system packages
echo ""
echo "[3/5] Installing system dependencies..."
sudo apt-get install -y build-essential python3-dev

# Install Python dependencies
echo ""
echo "[4/5] Checking Python packages..."
if [ -f "requirements.txt" ]; then
    # Check if Flask is already installed
    if python3 -c "import flask" &> /dev/null; then
        FLASK_VERSION=$(python3 -c "import flask; print(flask.__version__)" 2>/dev/null)
        echo "Flask already installed: v$FLASK_VERSION"
        
        # Check other key packages
        MISSING_PACKAGES=0
        
        if ! python3 -c "import pandas" &> /dev/null; then
            echo "Missing: pandas"
            MISSING_PACKAGES=1
        fi
        
        if ! python3 -c "import numpy" &> /dev/null; then
            echo "Missing: numpy"
            MISSING_PACKAGES=1
        fi
        
        if ! python3 -c "import sklearn" &> /dev/null; then
            echo "Missing: scikit-learn"
            MISSING_PACKAGES=1
        fi
        
        if [ $MISSING_PACKAGES -eq 1 ]; then
            echo "Installing missing packages..."
            pip3 install -r requirements.txt
            echo "Missing packages installed"
        else
            echo "All required packages are already installed"
        fi
    else
        echo "Flask not found. Installing all packages..."
        pip3 install -r requirements.txt
        echo "Python packages installed successfully"
    fi
else
    echo "ERROR: requirements.txt not found"
    exit 1
fi

# Create necessary directories
echo ""
echo "[5/5] Creating directories..."
mkdir -p data/raw data/processed data/incoming logs
chmod 755 data logs

# Make scripts executable
chmod +x start.sh stop.sh setup.sh 2>/dev/null

echo ""
echo "========================================"
echo "  Setup Complete!"
echo "========================================"
echo ""
echo "To start the application:"
echo "  ./start.sh"
echo ""
echo "To stop the application:"
echo "  ./stop.sh"
echo ""
