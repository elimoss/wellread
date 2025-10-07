import asyncio
from typing import List, Dict, Any
from anthropic import Anthropic


class ClaudeSummarizer:
    def __init__(self, api_key: str):
        self.client = Anthropic(api_key=api_key)

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

Please provide a concise, insightful summary (2-4 sentences) that:
1. Explains the main contribution or finding
2. Highlights why it's relevant to the topics of interest
3. Notes any practical implications or applications

Keep the tone professional but engaging."""

        try:
            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            message = await loop.run_in_executor(
                None,
                lambda: self.client.messages.create(
                    model='claude-sonnet-4-5-20250929',
                    max_tokens=300,
                    messages=[{
                        'role': 'user',
                        'content': prompt
                    }]
                )
            )

            return message.content[0].text
        except Exception as error:
            print(f"Error summarizing item \"{item.get('title', 'Unknown')}\": {str(error)}")
            return f"Summary unavailable: {str(error)}"

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

        prompt = f"""Create a brief digest summary (3-4 sentences) for today's research roundup. Here are the curated items:

{items_list}

Topics of focus: {', '.join(topics)}

Provide an engaging overview that highlights key themes and noteworthy developments."""

        try:
            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            message = await loop.run_in_executor(
                None,
                lambda: self.client.messages.create(
                    model='claude-3-5-sonnet-20241022',
                    max_tokens=250,
                    messages=[{
                        'role': 'user',
                        'content': prompt
                    }]
                )
            )

            return message.content[0].text
        except Exception as error:
            print(f"Error generating digest: {str(error)}")
            return f"Found {len(items)} relevant items from your RSS feeds."
