"""
Configuration - Paths, limits, and feature flags
"""
import os
from pathlib import Path

# Environment-based root path
DATA_ROOT = os.getenv('LOGAPP_ROOT', os.path.join(os.getcwd(), 'data'))
APP_PORT = int(os.getenv('APP_PORT', '5000'))

# Directory structure
RAW_DIR = os.path.join(DATA_ROOT, 'raw')
PROCESSED_DIR = os.path.join(DATA_ROOT, 'processed')
INDEX_DIR = os.path.join(DATA_ROOT, 'index')
INCOMING_DIR = os.getenv('INCOMING_DIR', os.path.join(DATA_ROOT, 'incoming'))

# Database
DB_PATH = os.path.join(os.getcwd(), 'db', 'ledger.db')

# Limits
MAX_UPLOAD_SIZE = 200 * 1024 * 1024  # 200MB
CHUNK_SIZE = 5000  # lines per chunk
SEARCH_RESULT_LIMIT = 50

# Feature flags
ENABLE_FAISS = False  # Use TF-IDF by default
ENABLE_SAMPLING = True  # Sample very large files
SAMPLING_THRESHOLD = 100000  # events

# Noise patterns (can be overridden by noise_patterns.txt)
NOISE_PATTERNS = [
    'health check',
    'heartbeat',
    'ping',
    'keep-alive'
]

# Load noise patterns from file if exists
NOISE_PATTERNS_FILE = os.path.join(DATA_ROOT, 'noise_patterns.txt')
if os.path.exists(NOISE_PATTERNS_FILE):
    with open(NOISE_PATTERNS_FILE) as f:
        NOISE_PATTERNS.extend([line.strip() for line in f if line.strip()])

# Ensure directories exist
for dir_path in [DATA_ROOT, RAW_DIR, PROCESSED_DIR, INDEX_DIR, INCOMING_DIR, os.path.dirname(DB_PATH)]:
    Path(dir_path).mkdir(parents=True, exist_ok=True)
