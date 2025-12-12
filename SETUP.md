# Setup Guide - Log Analytics Platform

Complete setup instructions for Ubuntu servers.

## Prerequisites

- **Operating System**: Ubuntu 18.04 or higher (or any Debian-based Linux)
- **Python**: Version 3.8 or higher
- **RAM**: Minimum 512 MB (1 GB recommended)
- **Disk Space**: 1 GB free space
- **Network**: Port 5000 should be available

## Installation Steps

### Step 1: Copy Project to Server

**Option A: Using SCP (from local machine)**
```bash
scp -r log-analytics/ user@your-server:/home/user/
```

**Option B: Using Git (on server)**
```bash
cd /home/user
git clone https://github.com/bhattpawan/sample-logs.git
cd sample-logs/log-analytics
```

**Option C: Manual Upload**
Use FileZilla, WinSCP, or any SFTP client to upload the entire project folder.

### Step 2: Navigate to Project Directory

```bash
cd log-analytics
```

### Step 3: Make Scripts Executable

```bash
chmod +x *.sh
```

### Step 4: Run Setup Script

```bash
./setup.sh
```

**What setup.sh does:**
- ✓ Updates system package list
- ✓ Checks if Python 3 is installed (installs if missing)
- ✓ Checks if pip3 is installed (installs if missing)
- ✓ Installs build-essential and python3-dev
- ✓ Checks if Flask and packages are installed (installs only missing ones)
- ✓ Creates data directories (raw, processed, incoming)
- ✓ Creates logs directory
- ✓ Sets proper permissions

**Expected output:**
```
========================================
  Log Analytics - Setup
========================================

[1/5] Updating package list...
[2/5] Installing Python 3...
Python 3 already installed: Python 3.10.12
[3/5] Installing system dependencies...
[4/5] Checking Python packages...
Flask already installed: v2.2.5
All required packages are already installed
[5/5] Creating directories...

========================================
  Setup Complete!
========================================
```

### Step 5: Verify Installation

Check if all packages are installed:
```bash
python3 -c "import flask, pandas, numpy, sklearn; print('All packages OK')"
```

Check if directories were created:
```bash
ls -la data/ logs/
```

## Configuration (Optional)

### Change Port Number

Edit `config.py`:
```python
APP_PORT = 8080  # Change from default 5000
```

### Allow Remote Access

Edit `config.py`:
```python
APP_HOST = '0.0.0.0'  # Listen on all interfaces
```

Then open firewall:
```bash
sudo ufw allow 5000/tcp
```

### Adjust File Size Limits

Edit `config.py`:
```python
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB
```

## Starting the Application

```bash
./start.sh
```

Access at: `http://localhost:5000`

## Verification

### Check if Running
```bash
ps aux | grep "python.*app.py"
```

### Test HTTP Response
```bash
curl http://localhost:5000
```

### View Logs
```bash
tail -f logs/flask.log
```

## Common Installation Issues

### Issue: Python 3 not found
```bash
sudo apt-get update
sudo apt-get install -y python3 python3-pip
```

### Issue: Permission denied on scripts
```bash
chmod +x *.sh
```

### Issue: pip install fails
```bash
# Try with --user flag
pip3 install --user -r requirements.txt

# Or upgrade pip first
python3 -m pip install --upgrade pip
pip3 install -r requirements.txt
```

### Issue: Port 5000 already in use
```bash
# Find what's using the port
sudo lsof -i :5000

# Kill the process
sudo kill -9 <PID>
```

### Issue: Cannot access from remote machine
```bash
# Check if Flask is listening on 0.0.0.0
netstat -tuln | grep 5000

# Open firewall
sudo ufw allow 5000/tcp
sudo ufw status
```

## Post-Installation

After successful setup:

1. **Start application**: `./start.sh`
2. **Upload sample logs**: Go to http://localhost:5000/upload
3. **View insights**: Go to http://localhost:5000/insights
4. **Explore dashboard**: Go to http://localhost:5000/dashboard

## Uninstall (if needed)

```bash
# Stop application
./stop.sh

# Remove Python packages (optional)
pip3 uninstall -y -r requirements.txt

# Remove project directory
cd ..
rm -rf log-analytics
```

## Next Steps

- See **USAGE.md** for how to use the application
- See **TROUBLESHOOTING.md** for common issues
- See **README.md** for feature documentation
