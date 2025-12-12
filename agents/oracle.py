"""
Oracle Agent - Search and retrieval with TF-IDF cosine similarity
"""
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

class Oracle:
    def __init__(self, nexus):
        self.nexus = nexus
    
    def search(self, query, top_n=50, filters=None):
        """Search index with optional filters"""
        # Load index if not loaded
        if self.nexus.vectorizer is None:
            if not self.nexus.load_index():
                return {'success': False, 'reason': 'Index not built', 'results': []}
        
        # Transform query
        try:
            query_vec = self.nexus.vectorizer.transform([query])
        except:
            return {'success': False, 'reason': 'Query transformation failed', 'results': []}
        
        # Compute similarities
        similarities = cosine_similarity(query_vec, self.nexus.tfidf_matrix).flatten()
        
        # Get top indices
        top_indices = np.argsort(similarities)[::-1][:top_n * 2]  # Get extra for filtering
        
        results = []
        for idx in top_indices:
            if len(results) >= top_n:
                break
            
            score = float(similarities[idx])
            if score < 0.01:  # Threshold
                continue
            
            meta = self.nexus.docs_meta[idx]
            
            # Apply filters
            if filters:
                if filters.get('level') and meta.get('level') != filters['level']:
                    continue
                if filters.get('service') and meta.get('service') != filters['service']:
                    continue
                if filters.get('time_from') and meta.get('ts', '') < filters['time_from']:
                    continue
                if filters.get('time_to') and meta.get('ts', '') > filters['time_to']:
                    continue
            
            results.append({
                'score': round(score, 4),
                'file': meta.get('file', ''),
                'line': meta.get('line', 0),
                'timestamp': meta.get('ts', ''),
                'level': meta.get('level', ''),
                'service': meta.get('service', ''),
                'user': meta.get('user', ''),
                'ip': meta.get('ip', '')
            })
        
        return {
            'success': True,
            'query': query,
            'result_count': len(results),
            'results': results
        }
    
    def get_suggestions(self, query_prefix, limit=10):
        """Get query suggestions based on existing terms"""
        if self.nexus.vectorizer is None:
            if not self.nexus.load_index():
                return []
        
        vocab = list(self.nexus.vectorizer.vocabulary_.keys())
        matches = [term for term in vocab if term.startswith(query_prefix.lower())]
        return sorted(matches)[:limit]
