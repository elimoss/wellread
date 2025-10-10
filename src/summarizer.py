import asyncio
from typing import List, Dict, Any

import tenacity
from anthropic import Anthropic
from tqdm import tqdm


class ClaudeSummarizer:
    def __init__(self, api_key: str, summarization_model: str = "claude-sonnet-4-5-20250929"):
        self.client = Anthropic(api_key=api_key)
        self.summarization_model = summarization_model

    @tenacity.retry(
        wait=tenacity.wait_fixed(0.1),
        stop=tenacity.stop_after_attempt(10),
        reraise=True,
    )
    async def summarize_paper(self, item: Dict[str, Any], topics: List[str]) -> str:
        """Generate a summary for a single paper/item."""
        author_line = f"Author: {item['creator']}\n" if item.get('creator') else ""

        prompt = f"""You are analyzing an RSS feed item. Here are the details:

Title: {item.get('title', 'No title')}
Source: {item.get('feedSource', 'Unknown source')}
{author_line}
Content:
{item.get('description') or item.get('content') or 'No content available'}

Topics of interest: {', '.join(topics)}

The first line should identify the first author(s) and the last author as well as their institutional affiliation, if available. 
Follow this with a concise summary as 3 bullet points. Keep each bullet point to one concise sentence. Be direct and professional."""

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

        # Better error handling for empty content
        if not message.content:
            print(f"Empty content in API response. Stop reason: {message.stop_reason}.\n{message}\n{item.get('title')}")
            if message.stop_reason == 'refusal':
                return "Claude refused to summarize this one :("

        if len(message.content) == 0:
            print(f"No content blocks returned. Stop reason: {message.stop_reason}.\n{message}\n{item.get('title')}")
            if message.stop_reason == 'refusal':
                return "Claude refused to summarize this one :("

        # Check if first content block has text
        if not hasattr(message.content[0], 'text'):
            print(f"Content block has no text attribute. Type: {type(message.content[0])}.\n{message}\n{item.get('title')}")

        return message.content[0].text

    async def summarize_batch(self, items: List[Dict[str, Any]], topics: List[str], max_concurrent: int = 3) -> List[
        Dict[str, Any]]:
        """Summarize multiple items in batches."""
        results = []

        with tqdm(total=len(items), desc="Summarizing papers", unit="paper") as pbar:
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
                    pbar.update(1)

                # Rate limiting: wait between batches
                if i + max_concurrent < len(items):
                    await asyncio.sleep(1)

        return results
