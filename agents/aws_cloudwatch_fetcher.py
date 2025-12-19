"""
AWS CloudWatch Log Fetcher - LogSphere Agent
Fetches logs from AWS CloudWatch Logs using boto3 SDK

Features:
- Auto-discover all log groups if none specified
- IAM credentials support (Access Key, Secret Key, Session Token)
- Fetches all available logs (no time filtering)
- Saves to incoming directory as JSON for UI processing
"""

import json
import os
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable

logger = logging.getLogger(__name__)

class AWSCloudWatchFetcher:
    def __init__(self, config: Dict[str, Any]):
        self.access_key = config.get('awsAccessKey', '')
        self.secret_key = config.get('awsSecretKey', '')
        self.session_token = config.get('awsSessionToken', '')
        self.region = config.get('awsRegion', 'us-east-1')
        self.log_group = config.get('awsLogGroup', '')  # Optional
        self.limit = int(config.get('awsLimit', 1000))
        self.all_logs: List[Dict] = []
        self.client = None

    def _get_boto3_client(self):
        import boto3
        credentials = {
            'aws_access_key_id': self.access_key,
            'aws_secret_access_key': self.secret_key,
            'region_name': self.region
        }
        if self.session_token:
            credentials['aws_session_token'] = self.session_token
        return boto3.client('logs', **credentials)

    def _list_log_groups(self) -> List[str]:
        """List all available log groups."""
        log_groups = []
        try:
            paginator = self.client.get_paginator('describe_log_groups')
            for page in paginator.paginate():
                for group in page.get('logGroups', []):
                    log_groups.append(group['logGroupName'])
        except Exception as e:
            logger.error(f"Error listing log groups: {e}")
        return log_groups

    def _fetch_logs_from_group(self, log_group: str) -> List[Dict]:
        """Fetch logs from a specific log group."""
        logs = []
        try:
            paginator = self.client.get_paginator('filter_log_events')
            params = {
                'logGroupName': log_group,
                'limit': min(self.limit, 100)
            }
            
            event_count = 0
            for page in paginator.paginate(**params):
                for event in page.get('events', []):
                    log_entry = {
                        'timestamp': datetime.fromtimestamp(event['timestamp'] / 1000).isoformat(),
                        'message': event.get('message', ''),
                        'logGroup': log_group,
                        'logStream': event.get('logStreamName', ''),
                        'eventId': event.get('eventId', ''),
                        'source': 'aws_cloudwatch'
                    }
                    logs.append(log_entry)
                    event_count += 1
                    if event_count >= self.limit:
                        return logs
        except Exception as e:
            logger.error(f"Error fetching from {log_group}: {e}")
        return logs

    def fetch_logs(self, progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """Fetch logs from CloudWatch, auto-discovering log groups if not specified."""
        try:
            if progress_callback:
                progress_callback(10, "Connecting to AWS CloudWatch...")

            self.client = self._get_boto3_client()

            # Get log groups to fetch from
            if self.log_group:
                log_groups = [self.log_group]
                if progress_callback:
                    progress_callback(20, f"Fetching from log group: {self.log_group}")
            else:
                if progress_callback:
                    progress_callback(15, "Discovering available log groups...")
                log_groups = self._list_log_groups()
                if not log_groups:
                    return {'success': False, 'error': 'No log groups found in this region'}
                if progress_callback:
                    progress_callback(25, f"Found {len(log_groups)} log groups")

            # Fetch logs from each group
            total_groups = len(log_groups)
            for idx, group in enumerate(log_groups):
                if progress_callback:
                    pct = 30 + int((idx / total_groups) * 60)
                    progress_callback(pct, f"Fetching from {group}...")
                
                logs = self._fetch_logs_from_group(group)
                self.all_logs.extend(logs)
                
                if len(self.all_logs) >= self.limit:
                    break

            if progress_callback:
                progress_callback(95, f"Fetched {len(self.all_logs)} log events")

            # Save to incoming directory as JSON
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"aws_cloudwatch_{timestamp}.json"
            incoming_path = os.path.join('data', 'incoming', filename)
            os.makedirs(os.path.dirname(incoming_path), exist_ok=True)
            
            with open(incoming_path, 'w', encoding='utf-8') as f:
                json.dump(self.all_logs, f, indent=2, default=str)

            if progress_callback:
                progress_callback(100, "Fetch complete!")

            return {
                'success': True,
                'content': json.dumps(self.all_logs, indent=2, default=str),
                'events_count': len(self.all_logs),
                'log_groups_fetched': len(log_groups),
                'output_file': incoming_path,
                'source': 'aws_cloudwatch'
            }

        except Exception as e:
            logger.error(f"CloudWatch fetch error: {e}")
            return {'success': False, 'error': str(e), 'source': 'aws_cloudwatch'}


def fetch_from_cloudwatch(config: Dict[str, Any], progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
    fetcher = AWSCloudWatchFetcher(config)
    return fetcher.fetch_logs(progress_callback)