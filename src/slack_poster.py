import asyncio
from datetime import datetime
from typing import List, Dict, Any
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError


class SlackPoster:
    def __init__(self, token: str, webhook: str = None):
        self.client = WebClient(token=token)
        self.webhook = webhook

    async def post_digest(self, channel: str, digest: str, item_count: int) -> str:
        """Post the main digest message to Slack."""
        today = datetime.now().strftime('%m/%d/%Y')

        message = {
            'channel': channel,
            'text': f"📰 *Daily Research Digest* - {today}",
            'blocks': [
                {
                    'type': 'header',
                    'text': {
                        'type': 'plain_text',
                        'text': f"📰 Daily Research Digest - {today}"
                    }
                },
                {
                    'type': 'section',
                    'text': {
                        'type': 'mrkdwn',
                        'text': digest
                    }
                },
                {
                    'type': 'context',
                    'elements': [
                        {
                            'type': 'mrkdwn',
                            'text': f"Found *{item_count}* relevant items. Individual summaries below 👇"
                        }
                    ]
                }
            ]
        }

        try:
            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: self.client.chat_postMessage(**message)
            )
            return result['ts']  # Return the timestamp for threading
        except SlackApiError as error:
            print(f"Error posting digest: {error.response['error']}")
            raise error

    async def post_paper_with_summary(self, channel: str, thread_ts: str, paper: Dict[str, Any], index: int, total: int) -> str:
        """Post a single paper and its summary as a threaded reply."""
        try:
            # Truncate description if too long
            description = paper.get('description', 'No description available')
            if description and len(description) > 300:
                description = description[:300] + '...'

            # Format publication date
            pub_date = 'Unknown date'
            if paper.get('pubDate'):
                try:
                    if isinstance(paper['pubDate'], str):
                        from dateutil import parser as date_parser
                        parsed_date = date_parser.parse(paper['pubDate'])
                        pub_date = parsed_date.strftime('%m/%d/%Y')
                    else:
                        import time
                        parsed_date = datetime.fromtimestamp(time.mktime(paper['pubDate']))
                        pub_date = parsed_date.strftime('%m/%d/%Y')
                except Exception:
                    pub_date = 'Unknown date'

            # Post the main paper info
            paper_message = {
                'channel': channel,
                'thread_ts': thread_ts,
                'text': paper.get('title', 'No title'),
                'blocks': [
                    {
                        'type': 'section',
                        'text': {
                            'type': 'mrkdwn',
                            'text': f"*{index}/{total}: {paper.get('title', 'No title')}*\n\n{description}"
                        }
                    },
                    {
                        'type': 'section',
                        'fields': [
                            {
                                'type': 'mrkdwn',
                                'text': f"*Source:*\n{paper.get('feedSource', 'Unknown')}"
                            },
                            {
                                'type': 'mrkdwn',
                                'text': f"*Published:*\n{pub_date}"
                            }
                        ]
                    },
                    {
                        'type': 'section',
                        'text': {
                            'type': 'mrkdwn',
                            'text': f"🔗 <{paper.get('link', '')}|Read more>"
                        }
                    }
                ]
            }

            loop = asyncio.get_event_loop()
            paper_result = await loop.run_in_executor(
                None,
                lambda: self.client.chat_postMessage(**paper_message)
            )

            # Small delay between messages
            await asyncio.sleep(0.5)

            # Post the summary as a reply in the thread
            summary_message = {
                'channel': channel,
                'thread_ts': paper_result['ts'],  # Thread off the paper post
                'text': f"📝 Summary: {paper.get('summary', 'No summary available')}",
                'blocks': [
                    {
                        'type': 'section',
                        'text': {
                            'type': 'mrkdwn',
                            'text': f"📝 *AI Summary*\n\n{paper.get('summary', 'No summary available')}"
                        }
                    }
                ]
            }

            await loop.run_in_executor(
                None,
                lambda: self.client.chat_postMessage(**summary_message)
            )

            return paper_result['ts']
        except SlackApiError as error:
            print(f"Error posting paper \"{paper.get('title', 'Unknown')}\": {error.response['error']}")
            raise error

    async def post_all_papers(self, channel: str, digest_ts: str, papers: List[Dict[str, Any]]):
        """Post all papers with their summaries."""
        total = len(papers)

        for i, paper in enumerate(papers):
            await self.post_paper_with_summary(channel, digest_ts, paper, i + 1, total)

            # Rate limiting between papers
            if i < len(papers) - 1:
                await asyncio.sleep(1)

    async def post_complete_digest(self, channel: str, digest: str, papers: List[Dict[str, Any]]):
        """Post the complete digest with all papers."""
        print(f"Posting digest to channel {channel}...")

        # Post the main digest
        digest_ts = await self.post_digest(channel, digest, len(papers))

        print(f"Digest posted. Now posting {len(papers)} individual papers...")

        # Post each paper with its summary
        await self.post_all_papers(channel, digest_ts, papers)

        print('All papers posted successfully!')
