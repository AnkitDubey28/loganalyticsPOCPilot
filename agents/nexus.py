"""
Nexus Agent - Local indexing with TF-IDF (FAISS optional fallback)
"""
import os
import json
import pickle
import hashlib
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

class Nexus:
    def __init__(self, index_dir, ledger):
        self.index_dir = index_dir
        self.ledger = ledger
        self.vectorizer_path = os.path.join(index_dir, 'tfidf_vectorizer.pkl')
        self.matrix_path = os.path.join(index_dir, 'tfidf_matrix.pkl')
        self.docs_path = os.path.join(index_dir, 'docs_meta.json')
        self.hash_path = os.path.join(index_dir, 'content_hash.txt')
        
        self.vectorizer = None
        self.tfidf_matrix = None
        self.docs_meta = []
    
    def _compute_content_hash(self, processed_dir):
        """Hash processed files to detect changes"""
        hasher = hashlib.md5()
        for fpath in sorted(Path(processed_dir).glob('*.jsonl')):
            hasher.update(str(fpath.stat().st_mtime).encode())
            hasher.update(str(fpath.stat().st_size).encode())
        return hasher.hexdigest()
    
    def needs_rebuild(self, processed_dir):
        """Check if index needs rebuild"""
        if not os.path.exists(self.hash_path):
            return True
        
        with open(self.hash_path) as f:
            old_hash = f.read().strip()
        
        new_hash = self._compute_content_hash(processed_dir)
        return old_hash != new_hash
    
    def build_index(self, processed_dir):
        """Build TF-IDF index from processed JSONL files"""
        docs = []
        docs_meta = []
        
        # Load all processed events
        for fpath in Path(processed_dir).glob('*.jsonl'):
            with open(fpath, 'r', encoding='utf-8') as f:
                for line_no, line in enumerate(f, 1):
                    try:
                        event = json.loads(line)
                        text = event.get('message', '')
                        if not text or len(text.strip()) < 3:
                            continue
                        
                        docs.append(text)
                        docs_meta.append({
                            'file': fpath.name,
                            'line': line_no,
                            'ts': event.get('ts_event', ''),
                            'level': event.get('level', ''),
                            'service': event.get('service', ''),
                            'user': event.get('user', ''),
                            'ip': event.get('ip', '')
                        })
                    except:
                        continue
        
        if not docs:
            return {'success': False, 'reason': 'No documents to index'}
        
        # Build TF-IDF
        self.vectorizer = TfidfVectorizer(
            max_features=5000,
            stop_words='english',
            ngram_range=(1, 2),
            min_df=2,
            max_df=0.8
        )
        
        self.tfidf_matrix = self.vectorizer.fit_transform(docs)
        self.docs_meta = docs_meta
        
        # Save artifacts
        with open(self.vectorizer_path, 'wb') as f:
            pickle.dump(self.vectorizer, f)
        
        with open(self.matrix_path, 'wb') as f:
            pickle.dump(self.tfidf_matrix, f)
        
        with open(self.docs_path, 'w', encoding='utf-8') as f:
            json.dump(docs_meta, f)
        
        # Save hash
        content_hash = self._compute_content_hash(processed_dir)
        with open(self.hash_path, 'w') as f:
            f.write(content_hash)
        
        # Record in ledger
        self.ledger.record_index_build(
            doc_count=len(docs),
            vocab_size=len(self.vectorizer.vocabulary_),
            index_type='tfidf'
        )
        
        return {
            'success': True,
            'doc_count': len(docs),
            'vocab_size': len(self.vectorizer.vocabulary_)
        }
    
    def load_index(self):
        """Load existing index"""
        if not os.path.exists(self.vectorizer_path):
            return False
        
        try:
            with open(self.vectorizer_path, 'rb') as f:
                self.vectorizer = pickle.load(f)
            
            with open(self.matrix_path, 'rb') as f:
                self.tfidf_matrix = pickle.load(f)
            
            with open(self.docs_path, 'r', encoding='utf-8') as f:
                self.docs_meta = json.load(f)
            
            return True
        except:
            return False
    
    def get_index_stats(self):
        """Get current index statistics"""
        if self.vectorizer is None:
            if not self.load_index():
                return None
        
        return {
            'doc_count': len(self.docs_meta),
            'vocab_size': len(self.vectorizer.vocabulary_) if self.vectorizer else 0,
            'index_type': 'tfidf'
        }
