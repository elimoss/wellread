import asyncio
from typing import List, Dict, Any

import numpy as np
from openai import OpenAI
from tqdm import tqdm


class ContentCurator:
    def __init__(self, openai_api_key: str):
        self.client = OpenAI(api_key=openai_api_key)
        self.embedding_model = "text-embedding-3-small"
        self.topic_embeddings_cache = {}

    async def load_topics(self, topics_file: str = 'topics.txt') -> List[str]:
        """Load topics from a text file."""
        with open(topics_file, 'r', encoding='utf-8') as f:
            content = f.read()

        return [
            line.strip()
            for line in content.split('\n')
            if line.strip() and not line.strip().startswith('#')
        ]

    def get_embedding(self, text: str) -> List[float]:
        """Get OpenAI embedding for a text string."""
        response = self.client.embeddings.create(
            model=self.embedding_model,
            input=text
        )
        return response.data[0].embedding

    async def get_embedding_async(self, text: str) -> List[float]:
        """Get OpenAI embedding asynchronously."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.get_embedding, text)

    def cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        vec1_np = np.array(vec1)
        vec2_np = np.array(vec2)

        dot_product = np.dot(vec1_np, vec2_np)
        norm1 = np.linalg.norm(vec1_np)
        norm2 = np.linalg.norm(vec2_np)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return float(dot_product / (norm1 * norm2))

    async def calculate_relevance_score(self, item: Dict[str, Any], topic_embeddings: List[tuple[str, List[float]]]) -> float:
        """Calculate relevance score using semantic similarity."""
        # Get item text (title is most important)
        item_text = item.get('title', '')
        if not item_text:
            return 0.0

        # Get embedding for the item
        item_embedding = await self.get_embedding_async(item_text)

        # Calculate maximum similarity to any topic
        max_similarity = 0.0
        for topic, topic_embedding in topic_embeddings:
            similarity = self.cosine_similarity(item_embedding, topic_embedding)
            max_similarity = max(max_similarity, similarity)

        # Convert similarity (0-1) to a score (0-100)
        return max_similarity * 100

    async def curate_items(
        self,
        items: List[Dict[str, Any]],
        topics: List[str],
        min_score: float = 0.1,
        max_items: int = None
    ) -> List[Dict[str, Any]]:
        """Curate items by scoring based on semantic similarity to topics."""
        if not topics:
            return []

        # Get embeddings for all topics
        print(f"Getting embeddings for {len(topics)} topics...")
        topic_embeddings = []
        for topic in topics:
            if topic not in self.topic_embeddings_cache:
                self.topic_embeddings_cache[topic] = await self.get_embedding_async(topic)
            topic_embeddings.append((topic, self.topic_embeddings_cache[topic]))

        # Calculate relevance scores for all items
        print(f"Calculating relevance scores for {len(items)} items...")
        scored_items = []
        for item in tqdm(items, desc="Scoring items"):
            item_copy = item.copy()
            score = await self.calculate_relevance_score(item, topic_embeddings)
            item_copy['relevanceScore'] = score
            scored_items.append(item_copy)

        # Filter by minimum score
        filtered_items = [
            item for item in scored_items
            if item['relevanceScore'] >= min_score
        ]

        # Sort by relevance score (highest first)
        filtered_items.sort(key=lambda x: x['relevanceScore'], reverse=True)

        # Limit to max_items if specified
        if max_items and len(filtered_items) > max_items:
            filtered_items = filtered_items[:max_items]

        return filtered_items

    def group_by_relevance(self, curated_items: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Group items by relevance level (high, medium, low)."""
        # Using semantic similarity scores (0-100)
        high_relevance = [item for item in curated_items if item['relevanceScore'] >= 70]
        medium_relevance = [item for item in curated_items if 40 <= item['relevanceScore'] < 70]
        low_relevance = [item for item in curated_items if item['relevanceScore'] < 40]

        return {
            'high': high_relevance,
            'medium': medium_relevance,
            'low': low_relevance
        }
