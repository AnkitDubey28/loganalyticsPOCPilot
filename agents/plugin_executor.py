#!/usr/bin/env python
"""
Plugin Executor - LogSphere Agent
Fetches data from configured plugins using cloudProvider/serviceProvider dispatch

Supported cloud providers:
- AWS: S3, CloudWatch Logs, CloudTrail
- Azure: Blob Storage, Event Hub, Monitor
- GCP: Cloud Storage, Cloud Logging
- Other: Generic REST API, Webhooks
"""
import os
import sys
import json
import logging
import requests
from datetime import datetime
from typing import Dict, Any, Optional, Callable

# Configure logging
logger = logging.getLogger(__name__)


def fetch_from_azure_blob(config: Dict[str, Any], progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
    """Fetch logs from Azure Blob Storage using SAS token URL."""
    try:
        if progress_callback:
            progress_callback(10, "Connecting to Azure Blob Storage...")

        blob_url = config.get('apiEndpoint') or config.get('azureBlobUrl', '')
        if not blob_url:
            return {'success': False, 'error': 'No Azure Blob URL provided'}

        if progress_callback:
            progress_callback(30, "Downloading blob content...")

        response = requests.get(blob_url, stream=True, timeout=60)

        if response.status_code == 200:
            content = response.text
            if progress_callback:
                progress_callback(100, "Download complete!")
            return {'success': True, 'content': content, 'size': len(content), 'source': 'azure_blob'}
        else:
            return {'success': False, 'error': f'Failed to download: HTTP {response.status_code}'}

    except requests.Timeout:
        return {'success': False, 'error': 'Request timed out'}
    except Exception as e:
        logger.error(f"Azure Blob fetch error: {e}")
        return {'success': False, 'error': str(e)}


def fetch_from_azure_eventhub(config: Dict[str, Any], progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
    """Fetch logs from Azure Event Hub."""
    try:
        from agents.azure_eventhub_fetcher import fetch_from_eventhub
        return fetch_from_eventhub(config, progress_callback)
    except ImportError as e:
        return {'success': False, 'error': 'Azure Event Hub module not available. Install: pip install azure-eventhub'}
    except Exception as e:
        logger.error(f"Azure Event Hub fetch error: {e}")
        return {'success': False, 'error': str(e)}


def fetch_from_s3(config: Dict[str, Any], progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
    """Fetch logs from AWS S3 bucket."""
    try:
        import boto3
        from botocore.exceptions import ClientError, BotoCoreError

        if progress_callback:
            progress_callback(10, "Connecting to AWS S3...")

        s3_url = config.get('apiEndpoint') or config.get('s3Url', '')

        if s3_url and 'amazonaws.com' in s3_url and '?' in s3_url:
            if progress_callback:
                progress_callback(30, "Downloading from S3 (presigned URL)...")
            response = requests.get(s3_url, stream=True, timeout=60)
            if response.status_code == 200:
                content = response.text
                if progress_callback:
                    progress_callback(100, "Download complete!")
                return {'success': True, 'content': content, 'size': len(content), 'source': 's3_presigned'}
            return {'success': False, 'error': f'S3 presigned URL returned status {response.status_code}'}

        access_key = config.get('awsAccessKey')
        secret_key = config.get('awsSecretKey')
        session_token = config.get('awsSessionToken')
        region = config.get('awsRegion', 'us-east-1')
        bucket = config.get('s3Bucket') or config.get('awsLogGroup', '')
        key = config.get('s3Key') or config.get('s3ObjectKey', '')

        if not access_key or not secret_key:
            return {'success': False, 'error': 'AWS credentials (awsAccessKey, awsSecretKey) are required'}

        credentials = {'aws_access_key_id': access_key, 'aws_secret_access_key': secret_key, 'region_name': region}
        if session_token:
            credentials['aws_session_token'] = session_token

        s3_client = boto3.client('s3', **credentials)

        if progress_callback:
            progress_callback(50, "Fetching object from S3...")

        if key:
            obj = s3_client.get_object(Bucket=bucket, Key=key)
            content = obj['Body'].read().decode('utf-8')
        else:
            response = s3_client.list_objects_v2(Bucket=bucket, MaxKeys=10)
            objects = response.get('Contents', [])
            if not objects:
                return {'success': False, 'error': 'No objects found in bucket'}
            latest = sorted(objects, key=lambda x: x['LastModified'], reverse=True)[0]
            obj = s3_client.get_object(Bucket=bucket, Key=latest['Key'])
            content = obj['Body'].read().decode('utf-8')

        if progress_callback:
            progress_callback(100, "Download complete!")
        return {'success': True, 'content': content, 'size': len(content), 'source': 's3'}

    except Exception as e:
        logger.error(f"S3 fetch error: {e}")
        return {'success': False, 'error': str(e)}


def fetch_from_cloudwatch(config: Dict[str, Any], progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
    """Fetch logs from AWS CloudWatch Logs."""
    try:
        from agents.aws_cloudwatch_fetcher import AWSCloudWatchFetcher
        
        access_key = config.get('awsAccessKey')
        secret_key = config.get('awsSecretKey')
        
        if not access_key:
            return {'success': False, 'error': 'AWS Access Key (awsAccessKey) is required for CloudWatch'}
        if not secret_key:
            return {'success': False, 'error': 'AWS Secret Key (awsSecretKey) is required for CloudWatch'}
        
        fetcher = AWSCloudWatchFetcher(config)
        return fetcher.fetch_logs(progress_callback)
    except ImportError:
        return {'success': False, 'error': 'CloudWatch module not available. Install: pip install boto3'}
    except Exception as e:
        logger.error(f"CloudWatch fetch error: {e}")
        return {'success': False, 'error': str(e)}


def fetch_from_api(config: Dict[str, Any], progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
    """Fetch logs from generic REST API."""
    try:
        if progress_callback:
            progress_callback(10, "Connecting to API endpoint...")

        endpoint = config.get('apiEndpoint')
        api_key = config.get('apiKey')
        method = config.get('apiMethod', 'GET').upper()

        if not endpoint:
            return {'success': False, 'error': 'No API endpoint provided'}

        headers = {'User-Agent': 'LogSphere-Agent/1.0'}
        if api_key:
            headers['Authorization'] = api_key if api_key.startswith('Bearer ') else f'Bearer {api_key}'

        if progress_callback:
            progress_callback(50, "Fetching data from API...")

        if method == 'GET':
            response = requests.get(endpoint, headers=headers, timeout=30)
        else:
            response = requests.post(endpoint, headers=headers, json=config.get('apiBody', {}), timeout=30)

        if response.status_code == 200:
            if progress_callback:
                progress_callback(100, "Download complete!")
            return {'success': True, 'content': response.text, 'size': len(response.text), 'source': 'api'}
        return {'success': False, 'error': f'API returned status {response.status_code}'}

    except Exception as e:
        logger.error(f"API fetch error: {e}")
        return {'success': False, 'error': str(e)}


def execute_plugin(plugin_id: int, plugin_type: str, config: Dict[str, Any], progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
    """Execute a plugin to fetch data based on cloudProvider/serviceProvider."""
    if progress_callback:
        progress_callback(5, "Starting plugin execution...")

    cloud_provider = config.get('cloudProvider', '').lower()
    service_provider = config.get('serviceProvider', '').lower()
    aws_service = config.get('awsService', '').lower()
    azure_service = config.get('azureService', '').lower()
    endpoint = config.get('apiEndpoint', '').lower()

    logger.info(f"Executing plugin {plugin_id}: provider={cloud_provider}, service={service_provider}")

    if cloud_provider == 'aws' or 'amazonaws.com' in endpoint:
        service = service_provider or aws_service
        if service == 'cloudwatch':
            return fetch_from_cloudwatch(config, progress_callback)
        elif service in ['s3', 'cloudtrail']:
            return fetch_from_s3(config, progress_callback)
        return fetch_from_s3(config, progress_callback)

    elif cloud_provider == 'azure' or 'blob.core.windows.net' in endpoint or 'azure' in endpoint:
        service = service_provider or azure_service
        if service == 'eventhub':
            return fetch_from_azure_eventhub(config, progress_callback)
        elif service in ['blob', 'storage']:
            return fetch_from_azure_blob(config, progress_callback)
        return fetch_from_azure_blob(config, progress_callback)

    elif cloud_provider == 'gcp' or plugin_type in ['api', 'webhook', 'cloud-api']:
        return fetch_from_api(config, progress_callback)

    # Auto-detect from endpoint
    if 'blob.core.windows.net' in endpoint:
        return fetch_from_azure_blob(config, progress_callback)
    elif 'amazonaws.com' in endpoint or 's3' in endpoint:
        return fetch_from_s3(config, progress_callback)
    return fetch_from_api(config, progress_callback)


__all__ = ['execute_plugin', 'fetch_from_azure_blob', 'fetch_from_azure_eventhub', 'fetch_from_s3', 'fetch_from_cloudwatch', 'fetch_from_api']