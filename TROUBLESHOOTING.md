# Troubleshooting Guide - Log Analytics Platform

Common issues and their solutions.

## Installation Issues

### Python 3 Not Found

**Error:**
```
ERROR: Python 3 is not installed
```

**Solution:**
```bash
sudo apt-get update
sudo apt-get install -y python3 python3-pip python3-dev
python3 --version  # Verify installation
```

### pip3 Not Found

**Error:**
```
pip3: command not found
```

**Solution:**
```bash
sudo apt-get install -y python3-pip
pip3 --version  # Verify installation
```

### Permission Denied on Scripts

**Error:**
```
bash: ./start.sh: Permission denied
```

**Solution:**
```bash
chmod +x *.sh
./start.sh
```

### Package Installation Fails

**Error:**
```
ERROR: Could not install packages due to an EnvironmentError
```

**Solution 1: Install with --user flag**
```bash
pip3 install --user -r requirements.txt
```

**Solution 2: Upgrade pip**
```bash
python3 -m pip install --upgrade pip
pip3 install -r requirements.txt
```

**Solution 3: Install system dependencies**
```bash
sudo apt-get install -y build-essential python3-dev
pip3 install -r requirements.txt
```

## Application Startup Issues

### Port 5000 Already in Use

**Error:**
```
Address already in use
```

**Solution 1: Find and kill the process**
```bash
sudo lsof -i :5000
sudo kill -9 <PID>
./start.sh
```

**Solution 2: Change port**
Edit `config.py`:
```python
APP_PORT = 8080  # Use different port
```

### Application Already Running

**Error:**
```
Already running (PID: 12345)
```

**Solution:**
```bash
./stop.sh
./start.sh
```

### Application Starts But Not Accessible

**Symptom:** Cannot access http://localhost:5000

**Check 1: Verify process is running**
```bash
ps aux | grep "python.*app.py"
```

**Check 2: Check logs**
```bash
tail -f logs/flask.log
```

**Check 3: Test locally**
```bash
curl http://localhost:5000
```

**Check 4: Check firewall**
```bash
sudo ufw status
sudo ufw allow 5000/tcp
```

### Database Lock Error

**Error:**
```
sqlite3.OperationalError: database is locked
```

**Solution:**
```bash
./stop.sh
# Wait 5 seconds
./start.sh
```

If persists:
```bash
rm data/ledger.db
./start.sh
# Re-upload logs
```

## File Upload Issues

### File Too Large

**Error:**
```
File too large (max 50 MB)
```

**Solution:**
Edit `config.py`:
```python
MAX_FILE_SIZE = 100 * 1024 * 1024  # Increase to 100 MB
```

Then restart:
```bash
./stop.sh
./start.sh
```

### Invalid File Type

**Error:**
```
Invalid file type. Allowed: .json, .csv, .txt, .log, .zip
```

**Solution 1: Check file extension**
```bash
# Rename file if needed
mv mylog.dat mylog.txt
```

**Solution 2: Add extension to config.py**
```python
ALLOWED_EXTENSIONS = {'.json', '.csv', '.txt', '.log', '.zip', '.dat'}
```

### Upload Hangs or Times Out

**Symptom:** Upload never completes

**Solution 1: Check file size**
- Split large files into smaller chunks
- Use ZIP for multiple files

**Solution 2: Check server resources**
```bash
free -h  # Check available memory
df -h    # Check disk space
top      # Check CPU usage
```

**Solution 3: Disable sampling temporarily**
Edit `config.py`:
```python
ENABLE_SAMPLING = False  # Process all events
```

## Search Issues

### No Search Results

**Symptom:** Search returns 0 results

**Solution 1: Check if logs uploaded**
```bash
ls -lh data/processed/
```

**Solution 2: Rebuild search index**
```bash
curl -X POST http://localhost:5000/index/build
```

**Solution 3: Try broader search**
- Use single keywords instead of phrases
- Remove filters
- Check spelling

### Search Very Slow

**Symptom:** Search takes > 10 seconds

**Solution 1: Reduce result limit**
Edit search request or config.py:
```python
SEARCH_RESULT_LIMIT = 20  # Reduce from 50
```

**Solution 2: Use specific filters**
- Filter by time range
- Filter by log level
- Filter by service

**Solution 3: Check system resources**
```bash
top  # Check CPU/memory usage
```

## Insights Issues

### No Insights Generated

**Symptom:** Insights page shows "No events found"

**Solution:**
1. Ensure logs are uploaded
2. Check database:
```bash
sqlite3 data/ledger.db "SELECT COUNT(*) FROM events;"
```
3. Check logs for errors:
```bash
tail -50 logs/flask.log | grep -i error
```

### Cloud Provider Not Detected

**Symptom:** Shows "Other" instead of AWS/Azure/GCP

**Solution:**
The detection is based on log content. Ensure logs contain:

**For AWS:**
- Fields: eventName, eventSource, awsRegion
- Keywords: amazonaws.com, cloudtrail, s3

**For Azure:**
- Fields: operationName, resourceId, subscriptionId
- Keywords: azure, microsoft, windows.net

**For GCP:**
- Fields: protoPayload, logName, insertId
- Keywords: googleapis, gcp, google

**Manual override:** Edit the database:
```bash
sqlite3 data/ledger.db
UPDATE files SET cloud_type='aws' WHERE filename LIKE '%cloudtrail%';
.exit
```

### Cost Comparison Shows $0.00

**Symptom:** All costs show as zero

**Solution:**
This is normal if:
- No logs uploaded yet
- Log sizes are very small (< 1 MB)

To see realistic costs, upload larger log files or multiple files.

## Remote Access Issues

### Cannot Access from Another Machine

**Symptom:** http://server-ip:5000 doesn't work

**Solution 1: Configure Flask to listen on all interfaces**
Edit `config.py`:
```python
APP_HOST = '0.0.0.0'  # Instead of 'localhost'
```

**Solution 2: Open firewall**
```bash
sudo ufw allow 5000/tcp
sudo ufw reload
sudo ufw status
```

**Solution 3: Check if port is listening**
```bash
netstat -tuln | grep 5000
# Should show: 0.0.0.0:5000 not 127.0.0.1:5000
```

**Solution 4: Check security groups (if cloud VM)**
- AWS: Add inbound rule for port 5000
- Azure: Add NSG rule for port 5000
- GCP: Add firewall rule for port 5000

## Performance Issues

### High Memory Usage

**Symptom:** System becomes slow, out of memory errors

**Solution 1: Enable sampling**
Edit `config.py`:
```python
ENABLE_SAMPLING = True
SAMPLING_THRESHOLD = 5000  # Reduce from 10000
```

**Solution 2: Process logs in batches**
- Upload smaller batches of files
- Wait for processing to complete
- Clear old data periodically

**Solution 3: Add swap space**
```bash
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

### High CPU Usage

**Symptom:** CPU at 100%, slow response

**Solution 1: Check what's running**
```bash
top
# Press 'P' to sort by CPU
```

**Solution 2: Restart application**
```bash
./stop.sh
./start.sh
```

**Solution 3: Reduce concurrent uploads**
- Upload one file at a time
- Avoid large ZIP files with many files

### Disk Space Full

**Symptom:**
```
No space left on device
```

**Solution 1: Check disk usage**
```bash
df -h
du -sh data/* logs/*
```

**Solution 2: Clear old data**
```bash
./stop.sh
rm -rf data/raw/*
rm -rf data/processed/*
rm data/ledger.db
./start.sh
```

**Solution 3: Archive and remove**
```bash
tar -czf backup-$(date +%Y%m%d).tar.gz data/
mv backup-*.tar.gz /path/to/storage/
rm -rf data/*
```

## Dashboard Issues

### Charts Not Displaying

**Symptom:** Dashboard shows empty charts

**Solution 1: Check if data exists**
```bash
curl http://localhost:5000/api/dashboard
```

**Solution 2: Clear browser cache**
- Press Ctrl+F5 to hard refresh
- Clear browser cache
- Try different browser

**Solution 3: Check JavaScript errors**
- Open browser console (F12)
- Check for JavaScript errors
- Check if Chart.js loaded

### Dashboard Shows Old Data

**Symptom:** Uploaded new files but dashboard unchanged

**Solution:**
```bash
# Rebuild search index
curl -X POST http://localhost:5000/index/build

# Refresh dashboard page
# Press F5
```

## Getting More Help

### Check Application Logs
```bash
tail -100 logs/flask.log
```

### Check System Logs
```bash
sudo journalctl -xe
dmesg | tail
```

### Enable Debug Mode

Edit `app.py`:
```python
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=config.APP_PORT, debug=True)
```

Restart and check logs for detailed errors.

### Report Issues

If problem persists:
1. Check logs: `logs/flask.log`
2. Note your system: `uname -a`
3. Note Python version: `python3 --version`
4. Note error message
5. Create issue: https://github.com/bhattpawan/sample-logs/issues

Include:
- Operating system
- Python version
- Error message
- Steps to reproduce
- Relevant log excerpt
