# 🚀 Quick Start Guide - Ubuntu Server

Get the Log Analytics Platform running on Ubuntu in under 2 minutes!

## Prerequisites

- **Ubuntu Server** 18.04 or higher
- **Python 3.8+** and pip
- Port 5000 available

## First-Time Setup

### Step 1: Build the Docker Image (One-time only)
```bash
# 1. Copy project to Ubuntu server
scp -r log-analytics/ user@server:/home/user/

# 2. SSH into server
ssh user@server

# 3. Navigate to project
cd log-analytics

# 4. Make scripts executable
chmod +x *.sh

# 5. Run setup (one-time only)
./setup.sh
```

## Start the Application

```bash
./start.sh
```

The application will start on: **http://localhost:5000**
## 🎯 Usage

### Starting the Application

Simply run the start script:

**Windows:**
```powershell
.\start.ps1
```

**Linux/Mac:**
```bash
./start.sh
```

The script will:
- ✅ Check if Docker is running
- ✅ Create/start the container if needed
- ✅ Start the Flask application
- ✅ Verify everything is working

### Stopping the Application

**Windows:**
```powershell
.\stop.ps1
```
Daily Usage

### Start the Application
```bash
./start.sh
```

### Stop the Application
```bash
./stop.sh
```

- **setup.sh** - One-time setup (installs Python, dependencies)
- **start.sh** - Starts Flask application in background
- **stop.sh** - Stops Flask application gracefully
docker build -t ubuntu-python-flask:latest .
```

### Issue: Application not responding
**Solution:** Check the logs:
```bash
docker exec log-analytics-vm cat /tmp/flask.log
```

## 📁 Project Structure

```
log-analytics/
├── start.ps1          # Windows start script
├── stop.ps1           # Windows stop script
├── start.sh           # Linux/Mac start script
├── stop.sh            # Linux/Mac stop script
├── app.py             # Main Flask application
├── config.py          # Configuration
├── utils.py           # Utility functions
├── agents/            # Agent modules
│   ├── sentinel.py    # File validation
│   ├── ledger.py      # Database operations
│   ├── nexus.py       # Search indexing
│   ├── oracle.py      # Search queries
│   ├── cipher.py      # Insights & analytics
│   └── prism.py       # Dashboard data
├── templates/         # HTML templates
├── static/            # CSS, JS, images
├── data/              # Application data (created on first run)
│   ├── raw/           # Uploaded files
│   ├── processed/     # Processed logs
│   └── incoming/      # Local import folder
└── requirements.txt   # Python dependencies
```

## 🎨 Features

- **Upload**: Upload log files (JSON, CSV, TXT, ZIP)
- **Search**: Intelligent search with TF-IDF ranking
- **Insights**: Automatic anomaly detection and recommendations
- **Dashboard**: Real-time metrics and visualizations
- **Cloud Detection**: Automatic AWS/Azure/GCP log identification
- **Cost Analysis**: Cloud provider comparison with real-time pricing

## 📞 Support

For detailed documentation, see:
- `README.md` - Complete feature documentation
- `SETUP.txt` - Detailed setup instructions
- `LAUNCH.txt` - Running instructions

## 🌐 Accessing from Remote Machine

To access from another computer:

1. Edit `config.py`:
```python
APP_HOST = '0.0.0.0'  # Instead of 'localhost'
```

2. Open firewall:
```bash
sudo ufw allow 5000/tcp
```

3. Access at: `http://<server-ip>:5000`

---

**You're all set! Start analyzing logs! 📊**
