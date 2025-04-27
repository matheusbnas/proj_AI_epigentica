import os
import json
from datetime import datetime, timedelta

class SlidesCacheManager:
    def __init__(self, cache_dir="cache"):
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
        
    def get_cache_key(self, data):
        """Generate cache key based on content"""
        return str(hash(str(data)))
    
    def get_cached_slides(self, cache_key):
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")
        if not os.path.exists(cache_file):
            return None
            
        # Check if cache is still valid (24h)
        if datetime.fromtimestamp(os.path.getmtime(cache_file)) < datetime.now() - timedelta(hours=24):
            return None
            
        with open(cache_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def cache_slides(self, cache_key, slides_data):
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(slides_data, f, ensure_ascii=False)
