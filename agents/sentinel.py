"""
Sentinel Agent - File validation and safety checks
Validates uploads, checks types, sizes, and safely handles zip files.
"""
import os
import zipfile
import json
import mimetypes
from pathlib import Path

MAX_FILE_SIZE = 200 * 1024 * 1024  # 200MB
ALLOWED_EXTENSIONS = {'.json', '.csv', '.log', '.txt', '.zip'}
ALLOWED_MIMETYPES = {'application/json', 'text/csv', 'text/plain', 'application/zip'}

def validate_file(filename, file_bytes):
    """Validate uploaded file for type, size, and safety"""
    result = {
        'valid': True,
        'filename': filename,
        'size': len(file_bytes),
        'type': None,
        'reasons': [],
        'extracted_files': []
    }
    
    # Check size
    if len(file_bytes) > MAX_FILE_SIZE:
        result['valid'] = False
        result['reasons'].append(f'File exceeds {MAX_FILE_SIZE/(1024*1024)}MB limit')
        return result
    
    # Check extension
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        result['valid'] = False
        result['reasons'].append(f'Extension {ext} not allowed')
        return result
    
    result['type'] = ext.lstrip('.')
    
    # Validate ZIP files
    if ext == '.zip':
        try:
            import io
            with zipfile.ZipFile(io.BytesIO(file_bytes)) as zf:
                if zf.testzip() is not None:
                    result['valid'] = False
                    result['reasons'].append('Corrupted ZIP file')
                    return result
                
                # Check contents
                for member in zf.namelist():
                    member_ext = Path(member).suffix.lower()
                    if member_ext not in {'.json', '.csv', '.log', '.txt'}:
                        result['valid'] = False
                        result['reasons'].append(f'ZIP contains invalid file: {member}')
                        return result
                    result['extracted_files'].append(member)
                    
        except zipfile.BadZipFile:
            result['valid'] = False
            result['reasons'].append('Invalid ZIP file')
            return result
    
    # Enhanced cloud provider detection
    try:
        # Try to decode and analyze content
        content = file_bytes.decode('utf-8', errors='ignore')[:5000]  # First 5KB
        content_lower = content.lower()
        
        # For JSON files, check structure first
        if ext == '.json':
            try:
                data = json.loads(file_bytes.decode('utf-8', errors='ignore'))
                if isinstance(data, list) and len(data) > 0:
                    sample = data[0]
                    # Detect common cloud log fields
                    cloud_hints = {
                        'aws': ['eventName', 'eventSource', 'awsRegion', 'userIdentity', 'requestParameters', 'responseElements'],
                        'azure': ['operationName', 'resourceId', 'subscriptionId', 'tenantId', 'resourceGroupName', 'correlation'],
                        'gcp': ['protoPayload', 'resource', 'severity', 'logName', 'insertId', 'jsonPayload']
                    }
                    for cloud, fields in cloud_hints.items():
                        if sum(1 for f in fields if f in sample) >= 2:  # At least 2 matching fields
                            result['cloud_type'] = cloud
                            break
            except:
                pass
        
        # Content-based detection (works for all file types)
        if not result.get('cloud_type'):
            cloud_scores = {
                'aws': 0,
                'azure': 0,
                'gcp': 0
            }
            
            # AWS indicators
            aws_terms = ['cloudtrail', 'cloudwatch', 'amazonaws.com', 's3.', 'ec2', 'lambda', 'arn:aws:', 'eventname', 'requestid']
            cloud_scores['aws'] = sum(1 for term in aws_terms if term in content_lower)
            
            # Azure indicators
            azure_terms = ['azure', 'microsoft', 'windows.net', 'subscriptionid', 'resourceid', 'operationname', 'azurewebsites']
            cloud_scores['azure'] = sum(1 for term in azure_terms if term in content_lower)
            
            # GCP indicators
            gcp_terms = ['googleapis', 'google', 'gcp', 'cloud.google', 'protopayload', 'insertid', 'bigquery', 'compute.']
            cloud_scores['gcp'] = sum(1 for term in gcp_terms if term in content_lower)
            
            # Assign cloud type if score is significant
            max_score = max(cloud_scores.values())
            if max_score >= 2:  # At least 2 matching terms
                result['cloud_type'] = max(cloud_scores, key=cloud_scores.get)
    except:
        pass  # If detection fails, proceed without cloud_type
    
    result['reasons'].append('Validation passed')
    return result


def validate_local_folder(folder_path):
    """Scan local folder for valid log files"""
    if not os.path.exists(folder_path):
        return {'valid': False, 'reason': 'Folder not found', 'files': []}
    
    valid_files = []
    for root, _, files in os.walk(folder_path):
        for fname in files:
            ext = Path(fname).suffix.lower()
            if ext in ALLOWED_EXTENSIONS:
                fpath = os.path.join(root, fname)
                try:
                    size = os.path.getsize(fpath)
                    if size <= MAX_FILE_SIZE:
                        valid_files.append({
                            'name': fname,
                            'path': fpath,
                            'size': size,
                            'type': ext.lstrip('.')
                        })
                except:
                    pass
    
    return {'valid': True, 'files': valid_files}
