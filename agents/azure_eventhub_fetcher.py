"""
Azure Event Hub Log Fetcher - LogSphere Agent
Fetches logs from Azure Event Hub using the official azure-eventhub SDK

This module supports:
- Connection via SAS connection string
- Configurable consumer group and partition
- Checkpointing for reliable consumption
- Graceful shutdown on empty events
"""

import json
import os
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable

# Configure logging
logger = logging.getLogger(__name__)


class AzureEventHubFetcher:
    """
    Fetches log events from Azure Event Hub.
    
    Configuration parameters:
        - connection_str: SAS connection string for Event Hub namespace
        - eventhub_name: Name of the Event Hub
        - consumer_group: Consumer group (default: $Default)
        - partition_id: Partition ID to read from (default: "0")
        - max_wait_time: Maximum wait time for events in seconds (default: 10)
        - output_file: Path to save fetched logs (default: azure_logs.json)
        - max_empty_events: Number of empty event batches before stopping (default: 5)
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the Azure Event Hub fetcher.
        
        Args:
            config: Dictionary containing connection and fetch parameters
        """
        self.connection_str = config.get('azureEventHubConnectionString', '')
        self.eventhub_name = config.get('azureEventHubName', '')
        self.consumer_group = config.get('azureEventHubConsumerGroup', '$Default')
        self.partition_id = config.get('azureEventHubPartitionId', '0')
        self.max_wait_time = int(config.get('azureEventHubMaxWaitTime', 10))
        self.output_file = config.get('azureEventHubOutputFile', 'azure_logs.json')
        self.max_empty_events = int(config.get('maxEmptyEvents', 5))
        
        self.all_logs: List[Dict] = []
        self.empty_event_count = 0
        self.client = None
        self._should_stop = False
        
    def validate_config(self) -> Dict[str, Any]:
        """
        Validate the configuration parameters.
        
        Returns:
            Dict with 'valid' bool and 'errors' list
        """
        errors = []
        
        if not self.connection_str:
            errors.append("Azure Event Hub connection string is required")
        
        if not self.eventhub_name:
            errors.append("Azure Event Hub name is required")
            
        if self.max_wait_time < 1:
            errors.append("Max wait time must be at least 1 second")
            
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }
    
    def _on_event(self, partition_context, event) -> None:
        """
        Callback function for received events.
        
        Args:
            partition_context: Context for the partition
            event: The received event (may be None for empty batches)
        """
        if event:
            try:
                # Try to parse as JSON
                try:
                    event_data = event.body_as_json()
                except Exception:
                    # Fall back to string if not JSON
                    event_data = {
                        'body': event.body_as_str(),
                        'sequence_number': event.sequence_number,
                        'enqueued_time': str(event.enqueued_time) if event.enqueued_time else None,
                        'partition_key': event.partition_key,
                        'offset': event.offset
                    }
                
                # Add metadata
                event_data['_eventhub_metadata'] = {
                    'partition_id': partition_context.partition_id,
                    'consumer_group': partition_context.consumer_group,
                    'fetched_at': datetime.utcnow().isoformat()
                }
                
                self.all_logs.append(event_data)
                
                # Update checkpoint
                partition_context.update_checkpoint(event)
                
                # Reset empty counter
                self.empty_event_count = 0
                
                logger.debug(f"Received event: seq={event.sequence_number}")
                
            except Exception as e:
                logger.error(f"Error processing event: {e}")
        else:
            # Empty event batch
            self.empty_event_count += 1
            logger.debug(f"Empty event batch ({self.empty_event_count}/{self.max_empty_events})")
            
            if self.empty_event_count >= self.max_empty_events:
                logger.info("Max empty events reached, stopping fetch")
                self._should_stop = True
                if self.client:
                    self.client.close()
    
    def fetch_events(self, progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """
        Fetch events from Azure Event Hub.
        
        Args:
            progress_callback: Optional callback function(percent, message)
            
        Returns:
            Dict with success status, logs, and metadata
        """
        try:
            from azure.eventhub import EventHubConsumerClient
        except ImportError:
            return {
                'success': False,
                'error': 'azure-eventhub package not installed. Run: pip install azure-eventhub'
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
            progress_callback(10, "Connecting to Azure Event Hub...")
        
        try:
            # Create consumer client
            self.client = EventHubConsumerClient.from_connection_string(
                conn_str=self.connection_str,
                consumer_group=self.consumer_group,
                eventhub_name=self.eventhub_name
            )
            
            if progress_callback:
                progress_callback(30, f"Connected. Fetching from partition {self.partition_id}...")
            
            # Receive events
            # Note: receive() is blocking, so we use a timeout approach
            logger.info(f"Starting event fetch from partition {self.partition_id}")
            
            try:
                self.client.receive(
                    on_event=self._on_event,
                    partition_id=self.partition_id,
                    starting_position="-1",  # Start from beginning
                    max_wait_time=self.max_wait_time
                )
            except Exception as e:
                # This will be triggered when we close the client
                if not self._should_stop:
                    raise e
            
            if progress_callback:
                progress_callback(80, f"Fetched {len(self.all_logs)} events...")
            
            # Save to file
            output_path = self.output_file
            if not os.path.isabs(output_path):
                output_path = os.path.join('data', 'raw', output_path)
            
            os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(self.all_logs, f, indent=2, default=str)
            
            if progress_callback:
                progress_callback(100, "Fetch complete!")
            
            return {
                'success': True,
                'content': json.dumps(self.all_logs, indent=2, default=str),
                'events_count': len(self.all_logs),
                'output_file': output_path,
                'source': 'azure_eventhub',
                'partition_id': self.partition_id,
                'consumer_group': self.consumer_group
            }
            
        except Exception as e:
            logger.error(f"Error fetching from Event Hub: {e}")
            return {
                'success': False,
                'error': str(e),
                'source': 'azure_eventhub'
            }
        finally:
            if self.client:
                try:
                    self.client.close()
                except Exception:
                    pass


def fetch_from_eventhub(config: Dict[str, Any], progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
    """
    Convenience function to fetch logs from Azure Event Hub.
    
    Args:
        config: Configuration dictionary with Event Hub parameters
        progress_callback: Optional progress callback function
        
    Returns:
        Dict with fetch results
    """
    fetcher = AzureEventHubFetcher(config)
    return fetcher.fetch_events(progress_callback)


# Standalone execution for testing
if __name__ == '__main__':
    import sys
    
    print("╔═══════════════════════════════════════════════════════════════╗")
    print("║         Azure Event Hub Log Fetcher - LogSphere Agent        ║")
    print("╚═══════════════════════════════════════════════════════════════╝")
    print()
    
    # Test configuration - replace with actual values for testing
    test_config = {
        'azureEventHubConnectionString': os.environ.get('AZURE_EVENTHUB_CONNECTION_STRING', ''),
        'azureEventHubName': os.environ.get('AZURE_EVENTHUB_NAME', ''),
        'azureEventHubConsumerGroup': '$Default',
        'azureEventHubPartitionId': '0',
        'azureEventHubMaxWaitTime': 10,
        'azureEventHubOutputFile': 'azure_eventhub_logs.json'
    }
    
    if not test_config['azureEventHubConnectionString']:
        print("ERROR: Set AZURE_EVENTHUB_CONNECTION_STRING environment variable")
        sys.exit(1)
    
    if not test_config['azureEventHubName']:
        print("ERROR: Set AZURE_EVENTHUB_NAME environment variable")
        sys.exit(1)
    
    def progress(percent, message):
        print(f"[{percent:3d}%] {message}")
    
    result = fetch_from_eventhub(test_config, progress)
    
    if result['success']:
        print(f"\n✅ Successfully fetched {result.get('events_count', 0)} events")
        print(f"   Saved to: {result.get('output_file', 'N/A')}")
    else:
        print(f"\n❌ Error: {result.get('error', 'Unknown error')}")
