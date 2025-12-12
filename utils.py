"""
Utility functions - Parsing, normalization, chunking
"""
import json
import csv
import io
import zipfile
from datetime import datetime
from pathlib import Path

def parse_json_logs(file_bytes, filename):
    """Parse JSON/JSONL logs"""
    text = file_bytes.decode('utf-8', errors='ignore')
    events = []
    
    # Try JSON array first
    try:
        data = json.loads(text)
        if isinstance(data, list):
            for item in data:
                events.append(normalize_event(item, 'json'))
        elif isinstance(data, dict):
            events.append(normalize_event(data, 'json'))
        return events
    except:
        pass
    
    # Try JSONL
    for line_no, line in enumerate(text.split('\n'), 1):
        line = line.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
            events.append(normalize_event(event, 'jsonl'))
        except:
            # Treat as plain text
            events.append({
                'ts_event': datetime.utcnow().isoformat(),
                'level': 'INFO',
                'service': filename,
                'user': None,
                'ip': None,
                'message': line,
                'json': None
            })
    
    return events


def parse_csv_logs(file_bytes, filename):
    """Parse CSV logs"""
    text = file_bytes.decode('utf-8', errors='ignore')
    reader = csv.DictReader(io.StringIO(text))
    
    events = []
    for row in reader:
        events.append(normalize_event(row, 'csv'))
    
    return events


def parse_plain_logs(file_bytes, filename):
    """Parse plain text logs"""
    text = file_bytes.decode('utf-8', errors='ignore')
    events = []
    
    for line_no, line in enumerate(text.split('\n'), 1):
        line = line.strip()
        if not line or len(line) < 3:
            continue
        
        # Simple pattern matching for common log formats
        level = 'INFO'
        for lvl in ['ERROR', 'FATAL', 'CRITICAL', 'WARN', 'WARNING', 'DEBUG', 'TRACE']:
            if lvl in line.upper():
                level = lvl
                break
        
        events.append({
            'ts_event': datetime.utcnow().isoformat(),
            'level': level,
            'service': filename,
            'user': None,
            'ip': None,
            'message': line,
            'json': None
        })
    
    return events


def normalize_event(raw_event, source_type):
    """Normalize event to common schema"""
    normalized = {
        'ts_event': None,
        'level': 'INFO',
        'service': None,
        'user': None,
        'ip': None,
        'message': '',
        'json': json.dumps(raw_event) if isinstance(raw_event, dict) else None
    }
    
    if not isinstance(raw_event, dict):
        normalized['message'] = str(raw_event)
        return normalized
    
    # AWS CloudTrail / CloudWatch patterns
    if 'eventTime' in raw_event:
        normalized['ts_event'] = raw_event['eventTime']
    elif 'timestamp' in raw_event:
        normalized['ts_event'] = raw_event['timestamp']
    elif '@timestamp' in raw_event:
        normalized['ts_event'] = raw_event['@timestamp']
    elif 'time' in raw_event:
        normalized['ts_event'] = raw_event['time']
    
    # Azure patterns
    if 'operationName' in raw_event:
        normalized['service'] = raw_event.get('operationName', '')
    elif 'eventName' in raw_event:
        normalized['service'] = raw_event.get('eventName', '')
    elif 'service' in raw_event:
        normalized['service'] = raw_event.get('service', '')
    elif 'logName' in raw_event:
        normalized['service'] = raw_event.get('logName', '')
    
    # User identity
    if 'userIdentity' in raw_event:
        user_id = raw_event['userIdentity']
        if isinstance(user_id, dict):
            normalized['user'] = user_id.get('principalId') or user_id.get('userName') or user_id.get('arn')
        else:
            normalized['user'] = str(user_id)
    elif 'caller' in raw_event:
        normalized['user'] = raw_event.get('caller', '')
    elif 'user' in raw_event:
        normalized['user'] = raw_event.get('user', '')
    
    # IP address
    if 'sourceIPAddress' in raw_event:
        normalized['ip'] = raw_event.get('sourceIPAddress', '')
    elif 'ip' in raw_event:
        normalized['ip'] = raw_event.get('ip', '')
    elif 'clientIP' in raw_event:
        normalized['ip'] = raw_event.get('clientIP', '')
    
    # Log level
    if 'level' in raw_event:
        normalized['level'] = str(raw_event['level']).upper()
    elif 'severity' in raw_event:
        normalized['level'] = str(raw_event['severity']).upper()
    elif 'logLevel' in raw_event:
        normalized['level'] = str(raw_event['logLevel']).upper()
    
    # Message
    if 'message' in raw_event:
        normalized['message'] = raw_event.get('message', '')
    elif 'msg' in raw_event:
        normalized['message'] = raw_event.get('msg', '')
    elif 'text' in raw_event:
        normalized['message'] = raw_event.get('text', '')
    elif 'errorMessage' in raw_event:
        normalized['message'] = raw_event.get('errorMessage', '')
    else:
        # Fallback: stringify the whole event
        normalized['message'] = json.dumps(raw_event)
    
    # Ensure timestamp
    if not normalized['ts_event']:
        normalized['ts_event'] = datetime.utcnow().isoformat()
    
    return normalized


def extract_zip(file_bytes):
    """Extract files from ZIP archive"""
    extracted = []
    
    with zipfile.ZipFile(io.BytesIO(file_bytes)) as zf:
        for member in zf.namelist():
            if member.endswith('/'):  # Skip directories
                continue
            
            file_data = zf.read(member)
            extracted.append({
                'filename': Path(member).name,
                'content': file_data
            })
    
    return extracted


def chunk_iterator(items, chunk_size=1000):
    """Yield chunks of items"""
    for i in range(0, len(items), chunk_size):
        yield items[i:i + chunk_size]


def filter_noise(events, noise_patterns):
    """Filter out noise based on patterns"""
    filtered = []
    
    for event in events:
        message = event.get('message', '').lower()
        if not any(pattern.lower() in message for pattern in noise_patterns):
            filtered.append(event)
    
    return filtered
