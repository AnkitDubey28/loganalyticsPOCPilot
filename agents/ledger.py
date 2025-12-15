"""
Ledger Agent - SQLite-based tracking of files, events, and indexing metadata
"""
import sqlite3
import json
import os
from datetime import datetime
from contextlib import contextmanager

class Ledger:
    def __init__(self, db_path):
        self.db_path = db_path
        self._init_db()
    
    @contextmanager
    def get_connection(self):
        """Context manager for DB connections"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def _init_db(self):
        """Initialize database schema"""
        with self.get_connection() as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filename TEXT NOT NULL,
                    upload_time TEXT NOT NULL,
                    size INTEGER NOT NULL,
                    file_type TEXT,
                    status TEXT DEFAULT 'uploaded',
                    error_msg TEXT,
                    event_count INTEGER DEFAULT 0,
                    cloud_type TEXT
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_id INTEGER,
                    ts_event TEXT,
                    level TEXT,
                    service TEXT,
                    user_identity TEXT,
                    ip_address TEXT,
                    message TEXT,
                    json_data TEXT,
                    FOREIGN KEY(file_id) REFERENCES files(id)
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS index_meta (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    build_time TEXT NOT NULL,
                    doc_count INTEGER,
                    vocab_size INTEGER,
                    index_type TEXT DEFAULT 'tfidf'
                )
            ''')
            
            conn.execute('CREATE INDEX IF NOT EXISTS idx_events_ts ON events(ts_event)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_events_level ON events(level)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_events_service ON events(service)')
    
    def record_file(self, filename, size, file_type, cloud_type=None):
        """Record uploaded file"""
        with self.get_connection() as conn:
            cursor = conn.execute('''
                INSERT INTO files (filename, upload_time, size, file_type, cloud_type)
                VALUES (?, ?, ?, ?, ?)
            ''', (filename, datetime.utcnow().isoformat(), size, file_type, cloud_type))
            return cursor.lastrowid
    
    def update_file_status(self, file_id, status, error_msg=None, event_count=None):
        """Update file processing status"""
        with self.get_connection() as conn:
            if event_count is not None:
                conn.execute('''
                    UPDATE files SET status=?, error_msg=?, event_count=? WHERE id=?
                ''', (status, error_msg, event_count, file_id))
            else:
                conn.execute('''
                    UPDATE files SET status=?, error_msg=? WHERE id=?
                ''', (status, error_msg, file_id))
    
    def add_events(self, events):
        """Batch insert events"""
        with self.get_connection() as conn:
            conn.executemany('''
                INSERT INTO events (file_id, ts_event, level, service, user_identity, ip_address, message, json_data)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', events)
    
    def list_files(self):
        """Get all files with stats"""
        with self.get_connection() as conn:
            cursor = conn.execute('''
                SELECT id, filename, upload_time, size, file_type, status, event_count, cloud_type
                FROM files ORDER BY upload_time DESC
            ''')
            return [dict(row) for row in cursor.fetchall()]
    
    def list_events(self, filters=None, limit=1000):
        """Query events with optional filters"""
        query = 'SELECT * FROM events WHERE 1=1'
        params = []
        
        if filters:
            if filters.get('time_from'):
                query += ' AND ts_event >= ?'
                params.append(filters['time_from'])
            if filters.get('time_to'):
                query += ' AND ts_event <= ?'
                params.append(filters['time_to'])
            if filters.get('level'):
                query += ' AND level = ?'
                params.append(filters['level'])
            if filters.get('service'):
                query += ' AND service = ?'
                params.append(filters['service'])
        
        query += f' ORDER BY ts_event DESC LIMIT {limit}'
        
        with self.get_connection() as conn:
            cursor = conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    def record_index_build(self, doc_count, vocab_size, index_type='tfidf'):
        """Record index metadata"""
        with self.get_connection() as conn:
            conn.execute('''
                INSERT INTO index_meta (build_time, doc_count, vocab_size, index_type)
                VALUES (?, ?, ?, ?)
            ''', (datetime.utcnow().isoformat(), doc_count, vocab_size, index_type))
    
    def get_latest_index_meta(self):
        """Get most recent index build info"""
        with self.get_connection() as conn:
            cursor = conn.execute('''
                SELECT * FROM index_meta ORDER BY build_time DESC LIMIT 1
            ''')
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_stats(self):
        """Get overall statistics"""
        with self.get_connection() as conn:
            stats = {}
            cursor = conn.execute('SELECT COUNT(*) as cnt FROM files')
            stats['total_files'] = cursor.fetchone()[0]
            
            cursor = conn.execute('SELECT COUNT(*) as cnt FROM events')
            stats['total_events'] = cursor.fetchone()[0]
            
            cursor = conn.execute("SELECT COUNT(*) as cnt FROM events WHERE level IN ('ERROR', 'FATAL', 'CRITICAL')")
            stats['error_count'] = cursor.fetchone()[0]
            
            cursor = conn.execute('SELECT SUM(size) as total FROM files')
            stats['total_size'] = cursor.fetchone()[0] or 0
            
            return stats


    def save_plugin(self, plugin_type, plugin_name, config):
        """Save plugin configuration"""
        import json
        cursor = self.conn.cursor()
        
        # Create plugins table if not exists
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS plugins (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                plugin_type TEXT NOT NULL,
                name TEXT NOT NULL,
                config TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'active'
            )
        ''')
        
        config_json = json.dumps(config)
        cursor.execute(
            "INSERT INTO plugins (plugin_type, name, config) VALUES (?, ?, ?)",
            (plugin_type, plugin_name, config_json)
        )
        self.conn.commit()
        return cursor.lastrowid
    
    def get_plugins(self):
        """Get all plugin configurations"""
        import json
        cursor = self.conn.cursor()
        
        # Ensure table exists
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS plugins (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                plugin_type TEXT NOT NULL,
                name TEXT NOT NULL,
                config TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'active'
            )
        ''')
        
        cursor.execute(
            "SELECT id, plugin_type, name, config, created_at, status FROM plugins WHERE status = 'active'"
        )
        rows = cursor.fetchall()
        
        plugins = []
        for row in rows:
            plugins.append({
                'id': row[0],
                'plugin_type': row[1],
                'name': row[2],
                'config': json.loads(row[3]) if row[3] else {},
                'created_at': row[4],
                'status': row[5]
            })
        
        return plugins
    
    def delete_plugin(self, plugin_id):
        """Delete a plugin (soft delete by setting status to deleted)"""
        cursor = self.conn.cursor()
        cursor.execute(
            "UPDATE plugins SET status = 'deleted' WHERE id = ?",
            (plugin_id,)
        )
        self.conn.commit()
        return cursor.rowcount > 0


    def save_plugin(self, plugin_type, plugin_name, config):
        """Save plugin configuration"""
        import json
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Create plugins table if not exists
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS plugins (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    plugin_type TEXT NOT NULL,
                    name TEXT NOT NULL,
                    config TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'active'
                )
            ''')
            
            config_json = json.dumps(config)
            cursor.execute(
                "INSERT INTO plugins (plugin_type, name, config) VALUES (?, ?, ?)",
                (plugin_type, plugin_name, config_json)
            )
            return cursor.lastrowid
    
    def get_plugins(self):
        """Get all plugin configurations"""
        import json
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Ensure table exists
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS plugins (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    plugin_type TEXT NOT NULL,
                    name TEXT NOT NULL,
                    config TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'active'
                )
            ''')
            
            cursor.execute(
                "SELECT id, plugin_type, name, config, created_at, status FROM plugins WHERE status = 'active'"
            )
            rows = cursor.fetchall()
            
            plugins = []
            for row in rows:
                plugins.append({
                    'id': row[0],
                    'plugin_type': row[1],
                    'name': row[2],
                    'config': json.loads(row[3]) if row[3] else {},
                    'created_at': row[4],
                    'status': row[5]
                })
            
            return plugins
    
    def delete_plugin(self, plugin_id):
        """Delete a plugin (soft delete by setting status to deleted)"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE plugins SET status = 'deleted' WHERE id = ?",
                (plugin_id,)
            )
            return cursor.rowcount > 0


