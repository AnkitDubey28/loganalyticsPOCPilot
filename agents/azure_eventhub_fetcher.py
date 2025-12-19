"""
Azure Event Hub Log Fetcher - LogSphere Agent
Fetches logs from Azure Event Hub with proper timeout handling

Features:
- Connection via SAS connection string
- Uses AmqpOverWebsocket transport for better connectivity
- Proper timeout after max_wait_time seconds
- Saves to incoming directory as JSON
"""

import json
import os
import logging
import threading
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable

logger = logging.getLogger(__name__)

class AzureEventHubFetcher:
    def __init__(self, config: Dict[str, Any]):
        self.connection_str = config.get('azureEventHubConnectionString', '')
        self.eventhub_name = config.get('azureEventHubName', '')
        self.consumer_group = config.get('azureEventHubConsumerGroup', '$Default')
        self.partition_id = config.get('azureEventHubPartitionId', '0')
        self.max_wait_time = int(config.get('azureEventHubMaxWaitTime', 30))
        self.all_logs: List[Dict] = []
        self._stop_event = threading.Event()

    def validate_config(self) -> Dict[str, Any]:
        errors = []
        if not self.connection_str:
            errors.append("Azure Event Hub connection string is required")
        if not self.eventhub_name:
            errors.append("Azure Event Hub name is required")
        return {'valid': len(errors) == 0, 'errors': errors}

    def fetch_events(self, progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        try:
            from azure.eventhub import EventHubConsumerClient, TransportType
        except ImportError:
            return {'success': False, 'error': 'azure-eventhub not installed. Run: pip install azure-eventhub'}

        validation = self.validate_config()
        if not validation['valid']:
            return {'success': False, 'error': validation['errors'][0]}

        if progress_callback:
            progress_callback(10, "Connecting to Azure Event Hub...")

        try:
            client = EventHubConsumerClient.from_connection_string(
                conn_str=self.connection_str,
                consumer_group=self.consumer_group,
                eventhub_name=self.eventhub_name,
                transport_type=TransportType.AmqpOverWebsocket
            )

            if progress_callback:
                progress_callback(30, f"Connected. Fetching from partition {self.partition_id}...")

            def on_event(partition_context, event):
                if event:
                    try:
                        try:
                            event_data = event.body_as_json()
                        except:
                            event_data = {'body': event.body_as_str()}
                        
                        event_data['_metadata'] = {
                            'partition_id': partition_context.partition_id,
                            'sequence_number': event.sequence_number,
                            'enqueued_time': str(event.enqueued_time) if event.enqueued_time else None,
                            'fetched_at': datetime.utcnow().isoformat(),
                            'source': 'azure_eventhub'
                        }
                        self.all_logs.append(event_data)
                        partition_context.update_checkpoint(event)
                    except Exception as e:
                        logger.error(f"Error processing event: {e}")

            def on_error(partition_context, error):
                logger.error(f"Event Hub error: {error}")

            # Use receive_batch with timeout for controlled execution
            def receive_with_timeout():
                try:
                    with client:
                        client.receive(
                            on_event=on_event,
                            on_error=on_error,
                            partition_id=self.partition_id,
                            starting_position="-1",
                            max_wait_time=5  # Short wait per batch
                        )
                except Exception as e:
                    if not self._stop_event.is_set():
                        logger.error(f"Receive error: {e}")

            # Start receiving in a thread with timeout
            receive_thread = threading.Thread(target=receive_with_timeout)
            receive_thread.daemon = True
            receive_thread.start()

            # Wait for max_wait_time seconds then stop
            receive_thread.join(timeout=self.max_wait_time)
            self._stop_event.set()
            
            try:
                client.close()
            except:
                pass

            if progress_callback:
                progress_callback(80, f"Fetched {len(self.all_logs)} events")

            # Save to incoming directory as JSON
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"azure_eventhub_{timestamp}.json"
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
                'output_file': incoming_path,
                'source': 'azure_eventhub'
            }

        except Exception as e:
            logger.error(f"Event Hub fetch error: {e}")
            return {'success': False, 'error': str(e), 'source': 'azure_eventhub'}


def fetch_from_eventhub(config: Dict[str, Any], progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
    fetcher = AzureEventHubFetcher(config)
    return fetcher.fetch_events(progress_callback)