#!/usr/bin/env python3

import os
import sys
import json
import asyncio
import traceback
from rss_parser import RSSFeedParser
from curator import ContentCurator
from summarizer import ClaudeSummarizer
from slack_poster import SlackPoster


async def main():
    print('🤖 WellRead Bot Starting...')

    # Load environment variables
    ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY')
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
    SLACK_TOKEN = os.environ.get('SLACK_BOT_TOKEN')
    SLACK_CHANNEL = os.environ.get('SLACK_CHANNEL')
    SLACK_WEBHOOK = os.environ.get('SLACK_WEBHOOK')

    if not ANTHROPIC_API_KEY:
        print('❌ ANTHROPIC_API_KEY environment variable is required')
        sys.exit(1)

    if not OPENAI_API_KEY:
        print('❌ OPENAI_API_KEY environment variable is required')
        sys.exit(1)

    if not SLACK_TOKEN or not SLACK_CHANNEL:
        print('❌ SLACK_BOT_TOKEN and SLACK_CHANNEL environment variables are required')
        sys.exit(1)

    # Load configuration
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
    except Exception:
        print('⚠️  Using default configuration')
        config = {
            'timeframe_hours': 24,
            'max_items': 20,
            'embedding_cache_dir': 'cache/embeddings',
            'llm_models': {
                'summarization': 'claude-sonnet-4-5-20250929',
                'digest': 'claude-sonnet-4-5-20250929'
            }
        }

    TIMEFRAME_HOURS = int(os.environ.get('TIMEFRAME_HOURS', config.get('timeframe_hours', 24)))
    MAX_ITEMS = int(os.environ.get('MAX_ITEMS', config.get('max_items', 20)))
    MIN_RELEVANCE_SCORE = float(os.environ.get('MIN_RELEVANCE_SCORE', config.get('min_relevance_score', 0.1)))
    EMBEDDING_CACHE_DIR = os.environ.get('EMBEDDING_CACHE_DIR', config.get('embedding_cache_dir', 'cache/embeddings'))

    # Get LLM model configurations
    llm_models = config.get('llm_models', {})
    SUMMARIZATION_MODEL = os.environ.get('SUMMARIZATION_MODEL', llm_models.get('summarization', 'claude-sonnet-4-5-20250929'))
    DIGEST_MODEL = os.environ.get('DIGEST_MODEL', llm_models.get('digest', 'claude-sonnet-4-5-20250929'))

    print(f'⏰ Looking for posts from the last {TIMEFRAME_HOURS} hours')
    print(f'📊 Maximum items to surface: {MAX_ITEMS}')
    print(f'🤖 Using models: {SUMMARIZATION_MODEL} (summaries), {DIGEST_MODEL} (digest)')

    # Initialize components
    feed_parser = RSSFeedParser()
    curator = ContentCurator(OPENAI_API_KEY, cache_dir=EMBEDDING_CACHE_DIR)

    try:
        # Step 1: Load feeds and topics
        print('📡 Loading RSS feeds...')
        feed_urls = await feed_parser.load_feeds('feeds.txt')
        print(f'Found {len(feed_urls)} feeds to monitor')

        print('🎯 Loading topics of interest...')
        topics = await curator.load_topics('topics.txt')
        print(f'Loaded {len(topics)} topics')

        if len(feed_urls) == 0:
            print('❌ No feeds configured in feeds.txt')
            sys.exit(1)

        if len(topics) == 0:
            print('❌ No topics configured in topics.txt')
            sys.exit(1)

        # Step 2: Fetch all RSS feeds
        print('🔍 Fetching RSS feeds...')
        all_items = await feed_parser.fetch_all_feeds(feed_urls)
        print(f'Fetched {len(all_items)} total items')

        # Step 3: Deduplicate by link URL
        print('🔗 Deduplicating items by link URL...')
        deduplicated_items = feed_parser.deduplicate_items(all_items)
        duplicates_removed = len(all_items) - len(deduplicated_items)
        print(f'{len(deduplicated_items)} unique items ({duplicates_removed} duplicates removed)')

        # Step 4: Filter by timeframe
        print(f'⏱️  Filtering items from last {TIMEFRAME_HOURS} hours...')
        recent_items = feed_parser.filter_by_timeframe(deduplicated_items, TIMEFRAME_HOURS)
        print(f'Found {len(recent_items)} recent items')

        if len(recent_items) == 0:
            print('✅ No new items to report')
            sys.exit(0)

        # Step 5: Curate based on topics using semantic similarity
        print('🔎 Curating content based on semantic similarity to topics...')
        curated_items = await curator.curate_items(recent_items, topics, min_score=MIN_RELEVANCE_SCORE, max_items=MAX_ITEMS)
        print(f'Curated {len(curated_items)} relevant items')

        if len(curated_items) == 0:
            print('✅ No relevant items found')
            sys.exit(0)

        # Initialize AI and Slack clients only when needed
        summarizer = ClaudeSummarizer(
            ANTHROPIC_API_KEY,
            summarization_model=SUMMARIZATION_MODEL,
            digest_model=DIGEST_MODEL
        )
        slack_poster = SlackPoster(SLACK_TOKEN, SLACK_WEBHOOK)

        # Step 6: Generate summaries
        print('✍️  Generating AI summaries...')
        items_with_summaries = await summarizer.summarize_batch(curated_items, topics)

        # Step 7: Generate digest
        print('📝 Generating digest...')
        digest = await summarizer.generate_digest(items_with_summaries, topics)

        # Step 8: Post to Slack
        print('📤 Posting to Slack...')
        await slack_poster.post_complete_digest(SLACK_CHANNEL, digest, items_with_summaries)

        print('✅ WellRead Bot completed successfully!')

    except Exception as error:
        print(f'❌ Error: {str(error)}')
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    asyncio.run(main())
