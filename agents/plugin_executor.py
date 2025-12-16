#!/usr/bin/env python
"""
Plugin Executor - Fetches data from configured plugins
"""
import os
import sys
import json
import requests
from datetime import datetime

def fetch_from_azure_blob(config, progress_callback=None):
    """Fetch logs from Azure Blob Storage using SAS token URL"""
    try:
        from azure.storage.blob import BlobServiceClient
        
        if progress_callback:
            progress_callback(10, "Connecting to Azure Blob Storage...")
        
        blob_url = config.get('apiEndpoint') or config.get('azureBlobUrl', '')
        if not blob_url:
            return {'success': False, 'error': 'No Azure Blob URL provided'}
        
        if progress_callback:
            progress_callback(30, "Downloading blob content...")
        
        # If it's a full blob URL with SAS token, download directly
        response = requests.get(blob_url, stream=True)
        
        if response.status_code == 200:
            content = response.text
            if progress_callback:
                progress_callback(100, "Download complete!")
            
            return {
                'success': True,
                'content': content,
                'size': len(content),
                'source': 'azure_blob'
            }
        else:
            return {
                'success': False,
                'error': f'Failed to download: HTTP {response.status_code}'
            }
            
    except Exception as e:
        return {'success': False, 'error': str(e)}

def fetch_from_s3(config, progress_callback=None):
    """Fetch logs from AWS S3 bucket"""
    try:
        import boto3
        from botocore.exceptions import ClientError
        
        if progress_callback:
            progress_callback(10, "Connecting to AWS S3...")
        
        # Check if it's a presigned URL or direct S3 URL
        s3_url = config.get('apiEndpoint') or config.get('s3Url', '')
        
        if 'amazonaws.com' in s3_url and '?' in s3_url:
            # Presigned URL - download directly
            if progress_callback:
                progress_callback(30, "Downloading from S3...")
            
            response = requests.get(s3_url, stream=True)
            if response.status_code == 200:
                content = response.text
                if progress_callback:
                    progress_callback(100, "Download complete!")
                
                return {
                    'success': True,
                    'content': content,
                    'size': len(content),
                    'source': 's3'
                }
        else:
            # Use boto3 with credentials
            access_key = config.get('awsAccessKey')
            secret_key = config.get('awsSecretKey')
            region = config.get('awsRegion', 'us-east-1')
            bucket = config.get('s3Bucket')
            key = config.get('s3Key')
            
            if not all([access_key, secret_key, bucket, key]):
                return {'success': False, 'error': 'Missing S3 credentials or bucket info'}
            
            s3_client = boto3.client(
                's3',
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
                region_name=region
            )
            
            if progress_callback:
                progress_callback(50, "Fetching object from S3...")
            
            obj = s3_client.get_object(Bucket=bucket, Key=key)
            content = obj['Body'].read().decode('utf-8')
            
            if progress_callback:
                progress_callback(100, "Download complete!")
            
            return {
                'success': True,
                'content': content,
                'size': len(content),
                'source': 's3'
            }
            
    except Exception as e:
        return {'success': False, 'error': str(e)}

def fetch_from_api(config, progress_callback=None):
    """Fetch logs from generic REST API"""
    try:
        if progress_callback:
            progress_callback(10, "Connecting to API endpoint...")
        
        endpoint = config.get('apiEndpoint')
        api_key = config.get('apiKey')
        method = config.get('apiMethod', 'GET').upper()
        
        if not endpoint:
            return {'success': False, 'error': 'No API endpoint provided'}
        
        headers = {}
        if api_key:
            if api_key.startswith('Bearer '):
                headers['Authorization'] = api_key
            else:
                headers['Authorization'] = f'Bearer {api_key}'
        
        if progress_callback:
            progress_callback(50, "Fetching data from API...")
        
        if method == 'GET':
            response = requests.get(endpoint, headers=headers, timeout=30)
        else:
            response = requests.post(endpoint, headers=headers, timeout=30)
        
        if response.status_code == 200:
            content = response.text
            if progress_callback:
                progress_callback(100, "Download complete!")
            
            return {
                'success': True,
                'content': content,
                'size': len(content),
                'source': 'api'
            }
        else:
            return {
                'success': False,
                'error': f'API returned status {response.status_code}'
            }
            
    except Exception as e:
        return {'success': False, 'error': str(e)}

def execute_plugin(plugin_id, plugin_type, config, progress_callback=None):
    """Execute a plugin to fetch data"""
    
    if progress_callback:
        progress_callback(5, "Starting plugin execution...")
    
    # Detect source type from config
    endpoint = config.get('apiEndpoint', '').lower()
    
    # Check if it's Azure Blob Storage
    if 'blob.core.windows.net' in endpoint or plugin_type == 'azure_blob':
        return fetch_from_azure_blob(config, progress_callback)
    
    # Check if it's S3
    elif 'amazonaws.com' in endpoint or 's3' in endpoint or plugin_type == 's3':
        return fetch_from_s3(config, progress_callback)
    
    # Generic REST API
    elif plugin_type in ['api', 'cloud-api']:
        return fetch_from_api(config, progress_callback)
    
    else:
        return {
            'success': False,
            'error': f'Unsupported plugin type: {plugin_type}'
        }

if __name__ == '__main__':
    # Test execution
    test_config = {
        'apiEndpoint': 'https://example.blob.core.windows.net/logs/app.log?sv=2023...',
    }
    
    def test_progress(percent, message):
        print(f"{percent}% - {message}")
    
    result = execute_plugin(1, 'api', test_config, test_progress)
    print(json.dumps(result, indent=2))
