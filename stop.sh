#!/bin/bash
echo "Stopping Flask..."
if [ -f ".flask.pid" ]; then
    PID=$(cat .flask.pid)
    if ps -p $PID > /dev/null 2>&1; then
        kill $PID
        sleep 2
        if ps -p $PID > /dev/null 2>&1; then
            kill -9 $PID
        fi
        rm .flask.pid
        echo "Stopped successfully"
    else
        rm .flask.pid
        echo "Not running"
    fi
else
    PID=$(pgrep -f "python.*app.py")
    if [ ! -z "$PID" ]; then
        kill $PID
        echo "Stopped successfully"
    else
        echo "Not running"
    fi
fi
