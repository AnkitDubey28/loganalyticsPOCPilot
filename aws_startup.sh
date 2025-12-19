#!/bin/bash
# LogSphere Agent - AWS EC2 Startup Script
# Run this script on AWS EC2 instances (Amazon Linux 2/Ubuntu)
# This script is idempotent - safe to run multiple times

set -e

echo "╔═══════════════════════════════════════════════════════════════════════╗"
echo "║                    LogSphere Agent - AWS Setup                        ║"
echo "║              Cloud Log Analytics Agent for EC2 Instances              ║"
echo "╚═══════════════════════════════════════════════════════════════════════╝"
echo ""

# Configuration
VENV_DIR="${LOGSPHERE_VENV:-/opt/logsphere-venv}"
APP_DIR="${LOGSPHERE_APP:-$(pwd)}"

# Detect OS
detect_os() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS=$ID
        VERSION=$VERSION_ID
    elif [ -f /etc/redhat-release ]; then
        OS="rhel"
    else
        OS="unknown"
    fi
    echo "Detected OS: $OS"
}

# Install system dependencies based on OS
install_system_deps() {
    echo ""
    echo "[1/5] Installing system dependencies..."
    
    case "$OS" in
        "amzn"|"rhel"|"centos"|"fedora")
            # Amazon Linux / RHEL / CentOS
            echo "Installing packages for Amazon Linux / RHEL..."
            sudo yum update -y -q
            sudo yum install -y -q python3 python3-pip python3-devel gcc gcc-c++ make
            ;;
        "ubuntu"|"debian")
            # Ubuntu / Debian
            echo "Installing packages for Ubuntu / Debian..."
            sudo apt-get update -qq
            sudo apt-get install -y -qq python3 python3-pip python3-venv python3-dev build-essential
            ;;
        *)
            echo "WARNING: Unknown OS. Attempting generic install..."
            if command -v apt-get &> /dev/null; then
                sudo apt-get update -qq
                sudo apt-get install -y -qq python3 python3-pip python3-venv python3-dev build-essential
            elif command -v yum &> /dev/null; then
                sudo yum install -y -q python3 python3-pip python3-devel gcc gcc-c++ make
            else
                echo "ERROR: Cannot determine package manager"
                exit 1
            fi
            ;;
    esac
    echo "System dependencies installed."
}

# Create or activate virtual environment
setup_venv() {
    echo ""
    echo "[2/5] Setting up Python virtual environment..."
    
    if [ -d "$VENV_DIR" ]; then
        echo "Virtual environment already exists at $VENV_DIR"
    else
        echo "Creating virtual environment at $VENV_DIR..."
        sudo mkdir -p "$(dirname "$VENV_DIR")"
        sudo python3 -m venv "$VENV_DIR"
        sudo chown -R $(whoami):$(whoami) "$VENV_DIR"
        echo "Virtual environment created."
    fi
    
    # Activate virtual environment
    source "$VENV_DIR/bin/activate"
    echo "Virtual environment activated."
    
    # Upgrade pip
    pip install --upgrade pip -q
}

# Install Python dependencies
install_python_deps() {
    echo ""
    echo "[3/5] Installing Python dependencies..."
    
    cd "$APP_DIR"
    
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt -q
        echo "Python dependencies installed."
    else
        echo "WARNING: requirements.txt not found in $APP_DIR"
    fi
    
    # Install AWS-specific packages
    pip install boto3 awscli -q
    echo "AWS SDK installed."
    
    # Install Azure SDK for Event Hub support
    pip install azure-eventhub azure-storage-blob -q
    echo "Azure SDK installed."
}

# Create directories
setup_directories() {
    echo ""
    echo "[4/5] Setting up directories..."
    
    cd "$APP_DIR"
    mkdir -p data/raw data/processed data/incoming logs
    chmod 755 data logs
    echo "Directories created."
}

# Start the application
start_app() {
    echo ""
    echo "[5/5] Starting LogSphere Agent..."
    
    cd "$APP_DIR"
    
    # Check if already running
    PID=$(pgrep -f "python.*app.py" || true)
    if [ ! -z "$PID" ]; then
        echo "LogSphere Agent is already running (PID: $PID)"
        echo "Stop with: kill $PID"
        return 0
    fi
    
    # Start the application
    source "$VENV_DIR/bin/activate"
    nohup python app.py > logs/logsphere.log 2>&1 &
    echo $! > .logsphere.pid
    
    sleep 3
    
    if [ -f ".logsphere.pid" ]; then
        NEW_PID=$(cat .logsphere.pid)
        if ps -p $NEW_PID > /dev/null 2>&1; then
            echo "LogSphere Agent started successfully (PID: $NEW_PID)"
        else
            echo "ERROR: Failed to start. Check logs/logsphere.log"
            exit 1
        fi
    fi
}

# Print completion message
print_completion() {
    echo ""
    echo "╔═══════════════════════════════════════════════════════════════════════╗"
    echo "║                    Setup Complete!                                     ║"
    echo "╚═══════════════════════════════════════════════════════════════════════╝"
    echo ""
    echo "LogSphere Agent is now running!"
    echo ""
    echo "  Access URL:    http://$(hostname -I | awk '{print $1}'):5000"
    echo "  Logs:          $APP_DIR/logs/logsphere.log"
    echo "  Virtual Env:   $VENV_DIR"
    echo ""
    echo "To activate the virtual environment manually:"
    echo "  source $VENV_DIR/bin/activate"
    echo ""
    echo "To stop the application:"
    echo "  kill \$(cat .logsphere.pid)"
    echo ""
}

# Main execution
main() {
    detect_os
    install_system_deps
    setup_venv
    install_python_deps
    setup_directories
    start_app
    print_completion
}

# Run main function
main "$@"
