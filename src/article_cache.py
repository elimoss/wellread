import json
import os
from typing import List, Dict, Any, Set
from datetime import datetime


class ArticleCache:
    """Manages cache of previously posted articles to avoid reposting."""

    def __init__(self, cache_file: str = "cache/posted_articles.json"):
        self.cache_file = cache_file
        self.posted_urls: Set[str] = set()
        self._load_cache()

    def _load_cache(self):
        """Load posted article URLs from cache file."""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.posted_urls = set(data.get('posted_urls', []))
            except Exception as e:
                print(f"Warning: Could not load article cache: {e}")
                self.posted_urls = set()
        else:
            # Create cache directory if it doesn't exist
            cache_dir = os.path.dirname(self.cache_file)
            if cache_dir and not os.path.exists(cache_dir):
                os.makedirs(cache_dir, exist_ok=True)

    def _save_cache(self):
        """Save posted article URLs to cache file."""
        try:
            cache_dir = os.path.dirname(self.cache_file)
            if cache_dir and not os.path.exists(cache_dir):
                os.makedirs(cache_dir, exist_ok=True)

            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'posted_urls': list(self.posted_urls),
                    'last_updated': datetime.now().isoformat()
                }, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save article cache: {e}")

    def is_posted(self, url: str) -> bool:
        """Check if an article URL has been posted before."""
        return url in self.posted_urls

    def mark_as_posted(self, url: str):
        """Mark an article URL as posted."""
        self.posted_urls.add(url)
        self._save_cache()

    def mark_batch_as_posted(self, urls: List[str]):
        """Mark multiple article URLs as posted."""
        self.posted_urls.update(urls)
        self._save_cache()

    def filter_unposted(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter out articles that have been posted before."""
        unposted = []
        for item in items:
            url = item.get('link', '')
            if url and not self.is_posted(url):
                unposted.append(item)
        return unposted

    def get_cache_size(self) -> int:
        """Get the number of cached article URLs."""
        return len(self.posted_urls)

    def clear_cache(self):
        """Clear all cached article URLs."""
        self.posted_urls = set()
        self._save_cache()
