# Usage Guide - Log Analytics Platform

Complete guide on how to use the Log Analytics Platform.

## Starting & Stopping

### Start Application
```bash
./start.sh
```
Access at: **http://localhost:5000**

### Stop Application
```bash
./stop.sh
```

### Check Status
```bash
# Check if running
ps aux | grep "python.*app.py"

# View logs
tail -f logs/flask.log
```

## Using the Application

### 1. Upload Logs

**Web Interface:**
1. Navigate to: http://localhost:5000/upload
2. Click "Choose Files" or drag & drop
3. Select log files (JSON, CSV, TXT, ZIP)
4. Click "Upload Files"
5. Wait for processing to complete

**Supported Formats:**
- **JSON**: CloudTrail, application logs, structured logs
- **CSV**: Comma-separated log exports
- **TXT/LOG**: Plain text logs
- **ZIP**: Archives containing multiple log files

**Cloud Provider Detection:**
The system automatically detects:
- ✓ AWS CloudTrail logs
- ✓ Azure Activity logs
- ✓ GCP Cloud Logging
- ✓ Other/On-premise logs

### 2. Search Logs

**Navigate to:** http://localhost:5000/search

**Search Features:**
- Full-text search using TF-IDF ranking
- Filter by log level (ERROR, WARN, INFO, DEBUG)
- Filter by service/component
- Filter by time range
- Results sorted by relevance

**Example Searches:**
```
"authentication failed"
"database connection timeout"
"error 500"
"user login"
```

**Using Filters:**
1. Enter search query
2. Select log level (optional)
3. Enter service name (optional)
4. Set time range (optional)
5. Click "Search"

### 3. View Insights

**Navigate to:** http://localhost:5000/insights

**What You'll See:**

**A. Key Metrics (Hero Cards)**
- Total errors with error rate
- Log volume and events per minute
- Traffic spikes detected

**B. Recommendations**
Each recommendation shows:
- Priority level (CRITICAL, HIGH, MEDIUM, LOW, INFO)
- Category (Error Rate, Traffic, Cost, Security, etc.)
- Impact description
- Cost impact analysis
- Action to take

**Example Recommendations:**
- High error rate detected → Review error services
- Traffic spikes found → Implement auto-scaling
- Log volume high → Use sampling/filtering
- Idle resources detected → Right-size infrastructure

**C. Cloud Provider Comparison**
- Side-by-side comparison of AWS, Azure, GCP, Other
- Your active provider highlighted with "✓ YOUR LOGS" badge
- Cost analysis:
  - Files processed
  - Events detected
  - Total size
  - Estimated monthly cost
  - Ingestion cost per GB
  - Storage cost per GB
- Key strengths of each platform
- Provider-specific cost-saving tips
- Real-time pricing data (when internet available)

**D. Knowledge Articles**
Contextual articles based on your logs:
- Error management best practices
- Performance optimization tips
- Cloud comparison guides
- Cost optimization strategies
- Security recommendations

### 4. View Dashboard

**Navigate to:** http://localhost:5000/dashboard

**Dashboard Components:**

**KPI Cards:**
- Total events processed
- Error count and percentage
- Files uploaded
- Services detected

**Charts:**
- Events over time (line chart)
- Log levels distribution (pie chart)
- Top services (bar chart)
- Top error messages (bar chart)

**Agent Activity Monitor:**
- Sentinel: File validation status
- Ledger: Database records
- Nexus: Search index status
- Oracle: Search queries
- Cipher: Insights computed
- Prism: Dashboard renders

## API Usage (Advanced)

### Upload Logs via API

```bash
curl -X POST http://localhost:5000/upload \
  -F "files=@logfile1.json" \
  -F "files=@logfile2.csv"
```

### Search via API

```bash
curl -X POST http://localhost:5000/api/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "authentication error",
    "level": "ERROR",
    "top_n": 10
  }'
```

### Get Insights via API

```bash
curl http://localhost:5000/api/insights
```

### Get Dashboard Data via API

```bash
curl http://localhost:5000/api/dashboard
```

## Workflow Examples

### Workflow 1: Analyzing AWS CloudTrail Logs

1. **Upload**: Upload CloudTrail JSON files
2. **Wait**: System detects AWS logs automatically
3. **Insights**: View AWS-specific recommendations
4. **Search**: Search for specific events (e.g., "UnauthorizedAccess")
5. **Dashboard**: Monitor error trends over time

### Workflow 2: Cost Optimization

1. **Upload**: Upload logs from multiple sources
2. **Insights**: Go to insights page
3. **Cloud Comparison**: Compare costs across providers
4. **Recommendations**: Review cost optimization tips
5. **Action**: Implement suggested changes

### Workflow 3: Security Audit

1. **Upload**: Upload security-related logs
2. **Search**: Search for "unauthorized", "failed", "denied"
3. **Insights**: Check compliance status
4. **Recommendations**: Review security recommendations
5. **Export**: Copy findings for audit report

## Tips & Best Practices

### Performance Tips
- Upload smaller batches (< 50 MB) for faster processing
- Use ZIP files for multiple small files
- Build search index after uploading all files
- Use filters in search to narrow results

### Cost Optimization
- Enable log sampling for high-volume logs (edit config.py)
- Filter out noise patterns (edit config.py)
- Review recommendations regularly
- Compare cloud providers before choosing

### Search Tips
- Use specific keywords for better results
- Combine multiple terms: "database connection failed"
- Use filters to narrow down results
- Check different log levels separately

### Troubleshooting
- If upload fails, check file size limits in config.py
- If search is slow, rebuild index: POST to /index/build
- If insights are empty, ensure logs are uploaded first
- Check logs/flask.log for errors

## Data Management

### Where Data is Stored

```
data/
├── raw/        # Original uploaded files
├── processed/  # Parsed and normalized logs (JSONL)
├── incoming/   # Local folder import (optional)
└── ledger.db   # SQLite database (metadata, events, index)

logs/
└── flask.log   # Application logs
```

### Backup Your Data

```bash
# Backup database and processed logs
tar -czf backup-$(date +%Y%m%d).tar.gz data/ logs/

# Restore from backup
tar -xzf backup-20251212.tar.gz
```

### Clear All Data

```bash
# Stop application first
./stop.sh

# Remove all data
rm -rf data/*
rm -f .flask.pid

# Restart
./start.sh
```

## Advanced Configuration

Edit `config.py` for advanced settings:

```python
# Application settings
APP_HOST = '0.0.0.0'  # Listen on all interfaces
APP_PORT = 5000       # Change port

# File limits
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB
ALLOWED_EXTENSIONS = {'.json', '.csv', '.txt', '.log', '.zip'}

# Sampling (for large logs)
ENABLE_SAMPLING = True
SAMPLING_THRESHOLD = 10000  # Keep only 10K events if more

# Search settings
SEARCH_RESULT_LIMIT = 50

# Noise filtering
NOISE_PATTERNS = ['DEBUG.*routine', 'healthcheck', 'ping']
```

## Getting Help

- Check **TROUBLESHOOTING.md** for common issues
- View logs: `tail -f logs/flask.log`
- Check GitHub issues: https://github.com/bhattpawan/sample-logs/issues
- Read **README.md** for feature documentation
