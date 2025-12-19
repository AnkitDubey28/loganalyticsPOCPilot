#!/bin/bash
echo "========================================"
echo "  LogSphere Agent - Starting"
echo "========================================"
echo ""
echo "[1/4] Checking Python..."
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed"
    exit 1
fi
echo "Found: $(python3 --version)"
echo ""
echo "[2/4] Checking dependencies..."
if [ -f "requirements.txt" ]; then
    pip3 install -q -r requirements.txt
fi
echo ""
echo "[3/4] Setting up directories..."
mkdir -p data/raw data/processed data/incoming logs
echo ""
echo "[4/4] Starting Flask..."
PID=$(pgrep -f "python.*app.py")
if [ ! -z "$PID" ]; then
    echo "Already running (PID: $PID)"
    exit 1
fi
nohup python3 app.py > logs/flask.log 2>&1 &
echo $! > .flask.pid
sleep 2
echo "Started successfully!"
echo ""
echo "Access at: http://localhost:5000"
echo "Stop with: ./stop.sh"
