"""
AWS CloudWatch Log Fetcher - LogSphere Agent
Fetches logs from AWS CloudWatch Logs using boto3 SDK

This module supports:
- IAM credentials (Access Key, Secret Key, Session Token)
- Log groups and log streams filtering
- Time-based filtering
- Pagination for large result sets
"""

import json
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable

# Configure logging
logger = logging.getLogger(__name__)


class AWSCloudWatchFetcher:
    """
    Fetches log events from AWS CloudWatch Logs.
    
    Configuration parameters:
        - awsAccessKey: AWS Access Key ID
        - awsSecretKey: AWS Secret Access Key
        - awsSessionToken: AWS Session Token (optional, for temporary credentials)
        - awsRegion: AWS Region (default: us-east-1)
        - awsLogGroup: CloudWatch Log Group name
        - awsLogStream: Specific log stream (optional)
        - awsStartTime: Start time for log query (optional, default: last 24 hours)
        - awsEndTime: End time for log query (optional, default: now)
        - awsLimit: Maximum number of log events to fetch (default: 10000)
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the AWS CloudWatch fetcher.
        
        Args:
            config: Dictionary containing AWS credentials and fetch parameters
        """
        self.access_key = config.get('awsAccessKey', '')
        self.secret_key = config.get('awsSecretKey', '')
        self.session_token = config.get('awsSessionToken', '')
        self.region = config.get('awsRegion', 'us-east-1')
        self.log_group = config.get('awsLogGroup', '')
        self.log_stream = config.get('awsLogStream', '')
        self.limit = int(config.get('awsLimit', 10000))
        
        # Time range (default: last 24 hours)
        self.start_time = config.get('awsStartTime')
        self.end_time = config.get('awsEndTime')
        
        self.all_logs: List[Dict] = []
        self.client = None
        
    def validate_config(self) -> Dict[str, Any]:
        """
        Validate the configuration parameters.
        
        Returns:
            Dict with 'valid' bool and 'errors' list
        """
        errors = []
        
        if not self.access_key:
            errors.append("AWS Access Key ID is required")
        
        if not self.secret_key:
            errors.append("AWS Secret Access Key is required")
            
        if not self.log_group:
            errors.append("CloudWatch Log Group name is required")
            
        if not self.region:
            errors.append("AWS Region is required")
            
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }
    
    def _get_boto3_client(self):
        """
        Create and return a boto3 CloudWatch Logs client.
        
        Returns:
            boto3 CloudWatch Logs client
        """
        import boto3
        
        # Build credentials dict
        credentials = {
            'aws_access_key_id': self.access_key,
            'aws_secret_access_key': self.secret_key,
            'region_name': self.region
        }
        
        # Add session token if provided (for temporary credentials)
        if self.session_token:
            credentials['aws_session_token'] = self.session_token
        
        return boto3.client('logs', **credentials)
    
    def _parse_timestamp(self, ts_value) -> Optional[int]:
        """
        Parse timestamp value to milliseconds since epoch.
        
        Args:
            ts_value: Timestamp as string, datetime, or epoch milliseconds
            
        Returns:
            Timestamp in milliseconds or None
        """
        if ts_value is None:
            return None
            
        if isinstance(ts_value, int):
            return ts_value
            
        if isinstance(ts_value, datetime):
            return int(ts_value.timestamp() * 1000)
            
        if isinstance(ts_value, str):
            try:
                dt = datetime.fromisoformat(ts_value.replace('Z', '+00:00'))
                return int(dt.timestamp() * 1000)
            except ValueError:
                pass
                
        return None
    
    def fetch_logs(self, progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """
        Fetch logs from AWS CloudWatch.
        
        Args:
            progress_callback: Optional callback function(percent, message)
            
        Returns:
            Dict with success status, logs, and metadata
        """
        try:
            import boto3
            from botocore.exceptions import ClientError, BotoCoreError
        except ImportError:
            return {
                'success': False,
                'error': 'boto3 package not installed. Run: pip install boto3'
            }
        
        # Validate configuration
        validation = self.validate_config()
        if not validation['valid']:
            return {
                'success': False,
                'error': 'Configuration validation failed',
                'details': validation['errors']
            }
        
        if progress_callback:
            progress_callback(10, "Connecting to AWS CloudWatch...")
        
        try:
            # Create client
            self.client = self._get_boto3_client()
            
            if progress_callback:
                progress_callback(20, f"Connected. Fetching from {self.log_group}...")
            
            # Calculate time range
            end_time_ms = self._parse_timestamp(self.end_time)
            if end_time_ms is None:
                end_time_ms = int(datetime.utcnow().timestamp() * 1000)
            
            start_time_ms = self._parse_timestamp(self.start_time)
            if start_time_ms is None:
                # Default: last 24 hours
                start_time_ms = end_time_ms - (24 * 60 * 60 * 1000)
            
            # Build request parameters
            params = {
                'logGroupName': self.log_group,
                'startTime': start_time_ms,
                'endTime': end_time_ms,
                'limit': min(self.limit, 10000)  # CloudWatch max is 10000
            }
            
            # Add log stream filter if specified
            if self.log_stream:
                params['logStreamNames'] = [self.log_stream]
            
            # Fetch logs with pagination
            all_events = []
            next_token = None
            page_count = 0
            
            while True:
                if next_token:
                    params['nextToken'] = next_token
                
                if progress_callback:
                    progress_callback(30 + min(page_count * 10, 50), 
                                     f"Fetching logs (page {page_count + 1})...")
                
                response = self.client.filter_log_events(**params)
                
                events = response.get('events', [])
                all_events.extend(events)
                
                logger.debug(f"Page {page_count + 1}: {len(events)} events")
                
                # Check for more pages
                next_token = response.get('nextToken')
                page_count += 1
                
                # Stop if no more pages or we've reached the limit
                if not next_token or len(all_events) >= self.limit:
                    break
            
            if progress_callback:
                progress_callback(80, f"Processing {len(all_events)} log events...")
            
            # Process events
            processed_events = []
            for event in all_events:
                try:
                    # Try to parse message as JSON
                    message = event.get('message', '')
                    try:
                        parsed_message = json.loads(message)
                    except json.JSONDecodeError:
                        parsed_message = message
                    
                    processed_event = {
                        'timestamp': datetime.fromtimestamp(
                            event.get('timestamp', 0) / 1000
                        ).isoformat(),
                        'ingestionTime': datetime.fromtimestamp(
                            event.get('ingestionTime', 0) / 1000
                        ).isoformat() if event.get('ingestionTime') else None,
                        'logStreamName': event.get('logStreamName', ''),
                        'message': parsed_message,
                        'eventId': event.get('eventId', ''),
                        '_cloudwatch_metadata': {
                            'log_group': self.log_group,
                            'region': self.region,
                            'fetched_at': datetime.utcnow().isoformat()
                        }
                    }
                    processed_events.append(processed_event)
                except Exception as e:
                    logger.warning(f"Error processing event: {e}")
                    processed_events.append(event)
            
            self.all_logs = processed_events
            
            # Save to file
            output_file = f"cloudwatch_{self.log_group.replace('/', '_')}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
            output_path = os.path.join('data', 'raw', output_file)
            
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(processed_events, f, indent=2, default=str)
            
            if progress_callback:
                progress_callback(100, "Fetch complete!")
            
            return {
                'success': True,
                'content': json.dumps(processed_events, indent=2, default=str),
                'events_count': len(processed_events),
                'output_file': output_path,
                'source': 'aws_cloudwatch',
                'log_group': self.log_group,
                'region': self.region,
                'time_range': {
                    'start': datetime.fromtimestamp(start_time_ms / 1000).isoformat(),
                    'end': datetime.fromtimestamp(end_time_ms / 1000).isoformat()
                }
            }
            
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            error_msg = e.response.get('Error', {}).get('Message', str(e))
            logger.error(f"AWS ClientError: {error_code} - {error_msg}")
            return {
                'success': False,
                'error': f"AWS Error ({error_code}): {error_msg}",
                'source': 'aws_cloudwatch'
            }
        except BotoCoreError as e:
            logger.error(f"AWS BotoCoreError: {e}")
            return {
                'success': False,
                'error': f"AWS Connection Error: {str(e)}",
                'source': 'aws_cloudwatch'
            }
        except Exception as e:
            logger.error(f"Error fetching from CloudWatch: {e}")
            return {
                'success': False,
                'error': str(e),
                'source': 'aws_cloudwatch'
            }


def fetch_from_cloudwatch(
    access_key: str,
    secret_key: str,
    session_token: Optional[str],
    region: str,
    log_group: str,
    log_stream: Optional[str] = None,
    start_time: Optional[Any] = None,
    end_time: Optional[Any] = None,
    limit: int = 10000,
    progress_callback: Optional[Callable] = None
) -> Dict[str, Any]:
    """
    Convenience function to fetch logs from AWS CloudWatch.
    
    Args:
        access_key: AWS Access Key ID
        secret_key: AWS Secret Access Key
        session_token: AWS Session Token (optional)
        region: AWS Region
        log_group: CloudWatch Log Group name
        log_stream: Specific log stream (optional)
        start_time: Start time for query (optional)
        end_time: End time for query (optional)
        limit: Maximum events to fetch
        progress_callback: Optional progress callback
        
    Returns:
        Dict with fetch results
    """
    config = {
        'awsAccessKey': access_key,
        'awsSecretKey': secret_key,
        'awsSessionToken': session_token,
        'awsRegion': region,
        'awsLogGroup': log_group,
        'awsLogStream': log_stream,
        'awsStartTime': start_time,
        'awsEndTime': end_time,
        'awsLimit': limit
    }
    
    fetcher = AWSCloudWatchFetcher(config)
    return fetcher.fetch_logs(progress_callback)


# Standalone execution for testing
if __name__ == '__main__':
    import sys
    
    print("╔═══════════════════════════════════════════════════════════════╗")
    print("║        AWS CloudWatch Log Fetcher - LogSphere Agent          ║")
    print("╚═══════════════════════════════════════════════════════════════╝")
    print()
    
    # Test configuration - use environment variables
    test_config = {
        'awsAccessKey': os.environ.get('AWS_ACCESS_KEY_ID', ''),
        'awsSecretKey': os.environ.get('AWS_SECRET_ACCESS_KEY', ''),
        'awsSessionToken': os.environ.get('AWS_SESSION_TOKEN', ''),
        'awsRegion': os.environ.get('AWS_REGION', 'us-east-1'),
        'awsLogGroup': os.environ.get('AWS_LOG_GROUP', ''),
        'awsLimit': 100
    }
    
    if not test_config['awsAccessKey']:
        print("ERROR: Set AWS_ACCESS_KEY_ID environment variable")
        sys.exit(1)
    
    if not test_config['awsSecretKey']:
        print("ERROR: Set AWS_SECRET_ACCESS_KEY environment variable")
        sys.exit(1)
        
    if not test_config['awsLogGroup']:
        print("ERROR: Set AWS_LOG_GROUP environment variable")
        sys.exit(1)
    
    def progress(percent, message):
        print(f"[{percent:3d}%] {message}")
    
    fetcher = AWSCloudWatchFetcher(test_config)
    result = fetcher.fetch_logs(progress)
    
    if result['success']:
        print(f"\n✅ Successfully fetched {result.get('events_count', 0)} events")
        print(f"   Log Group: {result.get('log_group', 'N/A')}")
        print(f"   Saved to: {result.get('output_file', 'N/A')}")
    else:
        print(f"\n❌ Error: {result.get('error', 'Unknown error')}")
