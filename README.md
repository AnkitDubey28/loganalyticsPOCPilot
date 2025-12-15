# Log Analytics Platform

A comprehensive offline log analysis platform powered by six intelligent agents, built with Flask and Python.

## 🤖 Six Intelligent Agents

1. **Sentinel** 🛡️ - File validation and safety checks
2. **Ledger** 📒 - SQLite-based metadata tracking
3. **Nexus** 🔗 - TF-IDF indexing for fast search
4. **Oracle** 🔮 - Intelligent search and retrieval
5. **Cipher** 🔐 - Insights, anomaly detection, recommendations
6. **Prism** 📊 - Real-time visualization and KPIs

## ✨ Features

- **Multi-format Support**: JSON, CSV, plain text, log files, ZIP archives
- **Cloud Log Detection**: Automatic detection of AWS CloudTrail, Azure, GCP logs
- **Offline Operation**: No cloud connectivity required
- **Visual Analytics**: Interactive dashboards with Chart.js
- **Smart Search**: TF-IDF based semantic search
- **Anomaly Detection**: MAD-based spike detection
- **Compliance Checks**: Built-in compliance monitoring
- **Cloud Comparison**: Compare logs across cloud providers

## 🚀 Quick Start (Ubuntu Server)

### Prerequisites
- Ubuntu 18.04 or higher
- Python 3.8+ and pip
- Port 5000 available

### Installation (3 Simple Steps)

```bash
# 1. Copy project to Ubuntu server
scp -r log-analytics/ user@server:/home/user/

# 2. Run setup (one-time only)
cd log-analytics
chmod +x *.sh
./setup.sh

# 3. Start application
./start.sh
```

### Access the Application

**Main URL**: http://localhost:5000

- **Upload**: Upload logs (JSON, CSV, TXT, ZIP)
- **Search**: Intelligent TF-IDF search
- **Insights**: Anomaly detection, recommendations, cost analysis  
- **Dashboard**: Real-time KPIs and charts

### Daily Usage

```bash
# Start application
./start.sh

# Stop application
./stop.sh

# View logs
tail -f logs/flask.log
```
- **Status**: Monitor processing and build index
- **Search**: Query logs with filters
- **Insights**: View recommendations and compliance

## 📁 Project Structure

```
log-analytics/
├── app.py                   # Flask application entry point
├── config.py                # Configuration and paths
├── utils.py                 # Parsing and normalization utilities
├── agents/                  # Six agent modules
│   ├── sentinel.py          # File validation
│   ├── ledger.py            # Database tracking
│   ├── nexus.py             # Index building
│   ├── oracle.py            # Search engine
│   ├── cipher.py            # Insights computation
│   └── prism.py             # Visualization data
├── templates/               # Jinja2 HTML templates
│   ├── base.html
│   ├── dashboard.html
│   ├── upload.html
│   ├── status.html
│   ├── search.html
│   └── insights.html
├── static/                  # Static assets
│   ├── css/styles.css
│   └── js/main.js
├── data/                    # Data storage
│   ├── raw/                 # Original uploads
│   ├── processed/           # Normalized JSONL
│   ├── index/               # TF-IDF artifacts
│   └── incoming/            # Server-side import folder
├── db/                      # SQLite database
│   └── ledger.db
├── requirements.txt         # Python dependencies
├── .env                     # Environment configuration
├── SETUP.txt                # Setup instructions
├── LAUNCH.txt               # Launch instructions
└── README.md                # This file
```

## 🎯 Usage Workflow

### 1. Upload Logs
- Click "Upload" in navigation
- Drag & drop files or click to browse
- OR click "Import from Local Folder" to scan `data/incoming/`
- Sentinel validates files and Ledger records metadata

### 2. Build Index
- Go to "Status" page
- Click "Build/Refresh Index"
- Nexus creates TF-IDF index from processed logs
- Index status displayed with document count and vocabulary size

### 3. Search Logs
- Go to "Search" page
- Enter query text
- Apply filters (time range, log level, service)
- Oracle returns ranked results with scores

### 4. View Insights
- Go to "Insights" page
- Cipher computes:
  - Error rates and distributions
  - Traffic spikes (anomaly detection)
  - Top services, users, IPs
  - Actionable recommendations
  - Compliance checks
  - Cloud provider comparison

### 5. Monitor Dashboard
- Go to "Dashboard" page
- Prism displays:
  - KPI cards (total events, error rate, ingestion size)
  - Error trend chart
  - Log level distribution
  - Top services and users
  - Hourly event distribution
  - Real-time agent activity

## 🔧 Configuration

### Environment Variables
```bash
LOGAPP_ROOT=./data          # Root data directory
APP_PORT=5000               # Flask port
FLASK_APP=app.py            # Flask app entry
FLASK_ENV=development       # Flask environment
```

### Limits (config.py)
- MAX_UPLOAD_SIZE: 200 MB
- CHUNK_SIZE: 5000 lines
- SEARCH_RESULT_LIMIT: 50
- SAMPLING_THRESHOLD: 100,000 events

### Noise Patterns
Create `data/noise_patterns.txt` to filter out benign log messages:
```
health check
heartbeat
ping
keep-alive
```

## 🌐 Supported Log Formats

### AWS CloudTrail/CloudWatch
```json
{
  "eventTime": "2025-12-11T10:00:00Z",
  "eventName": "ConsoleLogin",
  "userIdentity": {"principalId": "user123"},
  "sourceIPAddress": "192.168.1.1"
}
```

### Azure Logs
```json
{
  "time": "2025-12-11T10:00:00Z",
  "operationName": "Microsoft.Compute/virtualMachines/write",
  "caller": "admin@company.com"
}
```

### Plain Text Logs
```
2025-12-11 10:00:00 ERROR Service authentication failed
```

### CSV Logs
```csv
timestamp,level,service,message
2025-12-11 10:00:00,ERROR,AuthService,Login failed
```

## 📊 Agent Activity Monitoring

All pages display real-time agent status:
- **Sentinel**: Files validated
- **Ledger**: Events tracked
- **Nexus**: Documents indexed
- **Oracle**: Ready for queries
- **Cipher**: Insights computed
- **Prism**: Dashboards prepared

## 🔐 Security & Compliance

### Built-in Checks
- ✅ Logging coverage
- ✅ Timestamp presence
- ✅ User identity tracking
- ✅ File integrity validation
- ✅ Safe ZIP extraction

### Recommendations
- High priority for error rate >10%
- Medium priority for traffic anomalies
- Service health monitoring
- Resource utilization alerts

## 🎨 Visual Design

- Modern, responsive UI
- Dark navigation with white content cards
- Color-coded log levels and priorities
- Interactive charts with Chart.js
- Smooth animations and transitions
- Agent status indicators

## 📝 Code Statistics

- Total Python code: ~1,400 lines
- Agents: ~800 lines
- Flask app: ~300 lines
- Utils & config: ~300 lines
- Concise, well-commented code

## 🐛 Troubleshooting

### Port Already in Use
```bash
export APP_PORT=5001
python app.py
```

### Index Build Fails
- Ensure processed files exist in `data/processed/`
- Check file permissions
- View Flask console for errors

### No Search Results
- Build/refresh index first
- Check if events are ingested
- Try broader query terms

### Agent Shows Idle
- Upload files to activate Sentinel/Ledger
- Build index to activate Nexus
- Run search to activate Oracle
- Cipher/Prism activate with data presence

## 🔄 Development

### Adding New Cloud Providers
Edit `utils.py` `normalize_event()` to add field mappings.

### Customizing Visualizations
Edit `agents/prism.py` chart data preparation methods.

### Extending Search
Modify `agents/oracle.py` to add new ranking algorithms.

### Adding Compliance Checks
Add checks in `agents/cipher.py` `_check_compliance()`.

## 📦 Dependencies

- Flask 2.2.5 - Web framework
- Werkzeug 2.3.8 - WSGI utilities
- Pandas 2.0.3 - Data manipulation
- NumPy 1.24.3 - Numerical computing
- scikit-learn 1.3.0 - TF-IDF vectorization
- python-dateutil 2.8.2 - Date parsing

## 🎯 Important Notes

**Environment Adaptation**: This project automatically detects and merges configuration from:
- `.env` files
- `config.py`, `config.yaml`, `config.json`
- `noise_patterns.txt`
- `D:\LogAnalyticsEnv` (or `$LOGAPP_ROOT`)

**Non-Docker Project**: This is a regular Python/Flask application. We run it inside a Docker container for convenience, but it's not a Docker project itself. All code can be committed to Git as-is.

**Ubuntu Image Usage**: For local testing, we use the Ubuntu Docker image with Python 3.11 and Flask 2.2.5 that was set up earlier. Commands assume this environment.

**Main Web URL**: http://localhost:5000

## 📄 License

© 2025 Log Analytics Platform. All rights reserved.

## 🤝 Support

For issues or questions:
1. Check TROUBLESHOOTING section in LAUNCH.txt
2. Review Flask console logs
3. Verify agent status on any page
4. Ensure all dependencies are installed

---

**Powered by Six Intelligent Agents** 🤖🤖🤖🤖🤖🤖

---

**Last Updated:** December 15, 2025 - Plugin Configuration Feature Added & Tested

