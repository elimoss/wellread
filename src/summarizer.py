import asyncio
from typing import List, Dict, Any
from anthropic import Anthropic


class ClaudeSummarizer:
    def __init__(self, api_key: str, summarization_model: str = "claude-sonnet-4-5-20250929", digest_model: str = "claude-sonnet-4-5-20250929"):
        self.client = Anthropic(api_key=api_key)
        self.summarization_model = summarization_model
        self.digest_model = digest_model

    async def summarize_paper(self, item: Dict[str, Any], topics: List[str]) -> str:
        """Generate a summary for a single paper/item."""
        author_line = f"Author: {item['creator']}\n" if item.get('creator') else ""

        prompt = f"""You are analyzing an RSS feed item for a research digest. Here are the details:

Title: {item.get('title', 'No title')}
Source: {item.get('feedSource', 'Unknown source')}
{author_line}
Content:
{item.get('description') or item.get('content') or 'No content available'}

Topics of interest: {', '.join(topics)}

Provide a concise summary as 3 bullet points. Keep each bullet point to one concise sentence. Be direct and professional."""

        # Run in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        message = await loop.run_in_executor(
            None,
            lambda: self.client.messages.create(
                model=self.summarization_model,
                max_tokens=300,
                messages=[{
                    'role': 'user',
                    'content': prompt
                }]
            )
        )

        return message.content[0].text

    async def summarize_batch(self, items: List[Dict[str, Any]], topics: List[str], max_concurrent: int = 3) -> List[Dict[str, Any]]:
        """Summarize multiple items in batches."""
        results = []

        for i in range(0, len(items), max_concurrent):
            batch = items[i:i + max_concurrent]

            # Process batch concurrently
            summaries = await asyncio.gather(
                *[self.summarize_paper(item, topics) for item in batch]
            )

            # Add summaries to items
            for item, summary in zip(batch, summaries):
                result = item.copy()
                result['summary'] = summary
                results.append(result)

            # Rate limiting: wait between batches
            if i + max_concurrent < len(items):
                await asyncio.sleep(1)

        return results

    async def generate_digest(self, items: List[Dict[str, Any]], topics: List[str]) -> str:
        """Generate a digest summary for all items."""
        items_list = '\n'.join([
            f"{idx + 1}. {item.get('title', 'No title')} ({item.get('feedSource', 'Unknown source')})"
            for idx, item in enumerate(items[:20])
        ])

        prompt = f"""Create a bullet point list for today's research roundup. Bold keywords with asterisks. Be concise and professional.
Here are the curated items:

{items_list}

Topics of focus: {', '.join(topics)}

"""

        # Run in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        message = await loop.run_in_executor(
            None,
            lambda: self.client.messages.create(
                model=self.digest_model,
                max_tokens=250,
                messages=[{
                    'role': 'user',
                    'content': prompt
                }]
            )
        )

        return message.content[0].text
