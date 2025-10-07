import asyncio
from datetime import datetime
from typing import List, Dict, Any
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError


class SlackPoster:
    def __init__(self, token: str, webhook: str = None):
        self.client = WebClient(token=token)
        self.webhook = webhook

    async def post_header(self, channel: str) -> str:
        """Post a header message to separate from previous posts."""
        today = datetime.now().strftime('%B %d, %Y at %I:%M %p')

        message = {
            'channel': channel,
            'text': f"📰 WellRead Digest - {today}",
            'blocks': [
                {
                    'type': 'divider'
                },
                {
                    'type': 'header',
                    'text': {
                        'type': 'plain_text',
                        'text': f"📰 WellRead Digest"
                    }
                },
                {
                    'type': 'context',
                    'elements': [
                        {
                            'type': 'mrkdwn',
                            'text': f"_{today}_"
                        }
                    ]
                },
                {
                    'type': 'divider'
                }
            ]
        }

        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: self.client.chat_postMessage(**message)
            )
            return result['ts']
        except SlackApiError as error:
            print(f"Error posting header: {error.response['error']}")
            raise error

    async def post_paper_with_summary(self, channel: str, paper: Dict[str, Any], index: int, total: int) -> str:
        """Post a single paper as a top-level message with summary included."""
        try:
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

            # Get summary
            summary = paper.get('summary', 'No summary available')

            # Post the paper with summary as top-level message
            paper_message = {
                'channel': channel,
                'text': paper.get('title', 'No title'),
                'blocks': [
                    {
                        'type': 'section',
                        'text': {
                            'type': 'mrkdwn',
                            'text': f"*{index}/{total}: <{paper.get('link', '')}|{paper.get('title', 'No title')}>*\n\n{summary}"
                        }
                    },
                    {
                        'type': 'context',
                        'elements': [
                            {
                                'type': 'mrkdwn',
                                'text': f"*Source:* {paper.get('feedSource', 'Unknown')} | *Published:* {pub_date}"
                            }
                        ]
                    }
                ]
            }

            loop = asyncio.get_event_loop()
            paper_result = await loop.run_in_executor(
                None,
                lambda: self.client.chat_postMessage(**paper_message)
            )

            return paper_result['ts']
        except SlackApiError as error:
            print(f"Error posting paper \"{paper.get('title', 'Unknown')}\": {error.response['error']}")
            raise error

    async def post_all_papers(self, channel: str, papers: List[Dict[str, Any]]) -> List[str]:
        """Post all papers as top-level messages."""
        total = len(papers)
        timestamps = []

        for i, paper in enumerate(papers):
            ts = await self.post_paper_with_summary(channel, paper, i + 1, total)
            timestamps.append(ts)

            # Rate limiting between papers
            if i < len(papers) - 1:
                await asyncio.sleep(1)

        return timestamps

    async def post_digest_summary(self, channel: str, digest: str, item_count: int, paper_timestamps: List[str]) -> str:
        """Post the digest summary after all papers."""
        today = datetime.now().strftime('%m/%d/%Y')

        # Create links to the papers using their timestamps
        paper_links = '\n'.join([
            f"• <https://slack.com/archives/{channel}/p{ts.replace('.', '')}|Paper {i+1}>"
            for i, ts in enumerate(paper_timestamps[:10])  # Limit to first 10 links
        ])

        message = {
            'channel': channel,
            'text': f"📰 Daily Research Digest - {today}",
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
                        'text': f"*Summary of {item_count} curated items:*\n\n{digest}"
                    }
                },
                {
                    'type': 'divider'
                },
                {
                    'type': 'context',
                    'elements': [
                        {
                            'type': 'mrkdwn',
                            'text': f"Scroll up to see all {item_count} articles ☝️"
                        }
                    ]
                }
            ]
        }

        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: self.client.chat_postMessage(**message)
            )
            return result['ts']
        except SlackApiError as error:
            print(f"Error posting digest: {error.response['error']}")
            raise error

    async def post_complete_digest(self, channel: str, digest: str, papers: List[Dict[str, Any]]):
        """Post header, then all papers, then the digest summary."""
        print(f"Posting header to channel {channel}...")
        await self.post_header(channel)

        # Small delay after header
        await asyncio.sleep(1)

        print(f"Posting {len(papers)} papers...")

        # Post each paper as a top-level message
        paper_timestamps = await self.post_all_papers(channel, papers)

        print(f"All papers posted. Now posting digest summary...")

        # Post the digest after all papers
        await self.post_digest_summary(channel, digest, len(papers), paper_timestamps)

        print('Digest complete!')
