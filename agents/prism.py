"""
Prism Agent - Visualization data preparation and KPI computation
"""
import pandas as pd
from datetime import datetime, timedelta
from collections import Counter

class Prism:
    def __init__(self, ledger):
        self.ledger = ledger
    
    def get_dashboard_data(self):
        """Prepare all data for dashboard visualization"""
        stats = self.ledger.get_stats()
        events = self.ledger.list_events(limit=5000)
        
        if not events:
            return self._empty_dashboard()
        
        df = pd.DataFrame(events)
        
        # Parse timestamps
        if 'ts_event' in df.columns:
            try:
                df['ts_event'] = pd.to_datetime(df['ts_event'], errors='coerce')
                df = df.dropna(subset=['ts_event'])
            except:
                pass
        
        dashboard = {
            'kpis': self._compute_kpis(stats, df),
            'charts': {
                'errors_over_time': self._errors_over_time(df),
                'events_by_level': self._events_by_level(df),
                'top_services': self._top_services(df),
                'top_users': self._top_users(df),
                'hourly_distribution': self._hourly_distribution(df)
            }
        }
        
        return dashboard
    
    def _empty_dashboard(self):
        """Return empty dashboard structure"""
        return {
            'kpis': {
                'total_events': 0,
                'error_rate': 0,
                'ingestion_size_mb': 0,
                'files_processed': 0
            },
            'charts': {
                'errors_over_time': {'labels': [], 'data': []},
                'events_by_level': {'labels': [], 'data': []},
                'top_services': {'labels': [], 'data': []},
                'top_users': {'labels': [], 'data': []},
                'hourly_distribution': {'labels': [], 'data': []}
            }
        }
    
    def _compute_kpis(self, stats, df):
        """Compute key performance indicators"""
        errors = df[df['level'].isin(['ERROR', 'FATAL', 'CRITICAL', 'error', 'fatal', 'critical'])]
        
        return {
            'total_events': stats.get('total_events', 0),
            'error_rate': round(len(errors) / len(df) * 100, 2) if len(df) > 0 else 0,
            'ingestion_size_mb': round(stats.get('total_size', 0) / (1024*1024), 2),
            'files_processed': stats.get('total_files', 0),
            'error_count': len(errors),
            'services_count': df['service'].nunique() if 'service' in df.columns else 0
        }
    
    def _errors_over_time(self, df):
        """Error trend over time"""
        if 'ts_event' not in df.columns or len(df) == 0:
            return {'labels': [], 'data': []}
        
        errors = df[df['level'].isin(['ERROR', 'FATAL', 'CRITICAL', 'error', 'fatal', 'critical'])]
        
        if len(errors) == 0:
            return {'labels': [], 'data': []}
        
        errors_sorted = errors.sort_values('ts_event')
        errors_sorted['hour'] = errors_sorted['ts_event'].dt.floor('H')
        hourly = errors_sorted.groupby('hour').size()
        
        return {
            'labels': [str(h) for h in hourly.index],
            'data': [int(c) for c in hourly.values]
        }
    
    def _events_by_level(self, df):
        """Event distribution by log level"""
        if 'level' not in df.columns:
            return {'labels': [], 'data': []}
        
        level_counts = df['level'].value_counts()
        
        return {
            'labels': list(level_counts.index),
            'data': [int(c) for c in level_counts.values]
        }
    
    def _top_services(self, df):
        """Top services by event count"""
        if 'service' not in df.columns:
            return {'labels': [], 'data': []}
        
        top = df['service'].value_counts().head(10)
        
        return {
            'labels': list(top.index),
            'data': [int(c) for c in top.values]
        }
    
    def _top_users(self, df):
        """Top users by event count"""
        if 'user_identity' not in df.columns:
            return {'labels': [], 'data': []}
        
        top = df['user_identity'].dropna().value_counts().head(10)
        
        return {
            'labels': list(top.index),
            'data': [int(c) for c in top.values]
        }
    
    def _hourly_distribution(self, df):
        """Event distribution by hour of day"""
        if 'ts_event' not in df.columns or len(df) == 0:
            return {'labels': [], 'data': []}
        
        df['hour_of_day'] = df['ts_event'].dt.hour
        hourly = df.groupby('hour_of_day').size().reindex(range(24), fill_value=0)
        
        return {
            'labels': [f'{h:02d}:00' for h in range(24)],
            'data': [int(c) for c in hourly.values]
        }
    
    def get_agent_activity(self):
        """Track which agents have performed work"""
        index_meta = self.ledger.get_latest_index_meta()
        files = self.ledger.list_files()
        stats = self.ledger.get_stats()
        
        return {
            'Sentinel': {
                'status': 'active' if len(files) > 0 else 'idle',
                'work': f'Validated {len(files)} files',
                'icon': '🛡️'
            },
            'Ledger': {
                'status': 'active' if stats.get('total_events', 0) > 0 else 'idle',
                'work': f'Tracked {stats.get("total_events", 0)} events',
                'icon': '📒'
            },
            'Nexus': {
                'status': 'active' if index_meta else 'idle',
                'work': f'Indexed {index_meta.get("doc_count", 0)} docs' if index_meta else 'No index built',
                'icon': '🔗'
            },
            'Oracle': {
                'status': 'ready',
                'work': 'Ready for search queries',
                'icon': '🔮'
            },
            'Cipher': {
                'status': 'active' if stats.get('total_events', 0) > 0 else 'idle',
                'work': 'Insights computed',
                'icon': '🔐'
            },
            'Prism': {
                'status': 'active',
                'work': 'Dashboard data prepared',
                'icon': '📊'
            }
        }
