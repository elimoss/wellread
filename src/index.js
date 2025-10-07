#!/usr/bin/env node

import { RSSFeedParser } from './rss-parser.js';
import { ContentCurator } from './curator.js';
import { ClaudeSummarizer } from './summarizer.js';
import { SlackPoster } from './slack-poster.js';
import fs from 'fs/promises';
import path from 'path';

async function main() {
  console.log('🤖 WellRead Bot Starting...');

  // Load environment variables
  const ANTHROPIC_API_KEY = process.env.ANTHROPIC_API_KEY;
  const SLACK_TOKEN = process.env.SLACK_BOT_TOKEN;
  const SLACK_CHANNEL = process.env.SLACK_CHANNEL;
  const SLACK_WEBHOOK = process.env.SLACK_WEBHOOK;

  if (!ANTHROPIC_API_KEY) {
    console.error('❌ ANTHROPIC_API_KEY environment variable is required');
    process.exit(1);
  }

  if (!SLACK_TOKEN || !SLACK_CHANNEL) {
    console.error('❌ SLACK_BOT_TOKEN and SLACK_CHANNEL environment variables are required');
    process.exit(1);
  }

  // Load configuration
  let config;
  try {
    const configContent = await fs.readFile('config.json', 'utf-8');
    config = JSON.parse(configContent);
  } catch (error) {
    console.log('⚠️  Using default configuration');
    config = { timeframe_hours: 24 };
  }

  const TIMEFRAME_HOURS = parseInt(process.env.TIMEFRAME_HOURS || config.timeframe_hours || 24);

  console.log(`⏰ Looking for posts from the last ${TIMEFRAME_HOURS} hours`);

  // Initialize components
  const feedParser = new RSSFeedParser();
  const curator = new ContentCurator();
  const summarizer = new ClaudeSummarizer(ANTHROPIC_API_KEY);
  const slackPoster = new SlackPoster(SLACK_TOKEN, SLACK_WEBHOOK);

  try {
    // Step 1: Load feeds and topics
    console.log('📡 Loading RSS feeds...');
    const feedUrls = await feedParser.loadFeeds('feeds.txt');
    console.log(`Found ${feedUrls.length} feeds to monitor`);

    console.log('🎯 Loading topics of interest...');
    const topics = await curator.loadTopics('topics.txt');
    console.log(`Loaded ${topics.length} topics`);

    if (feedUrls.length === 0) {
      console.error('❌ No feeds configured in feeds.txt');
      process.exit(1);
    }

    if (topics.length === 0) {
      console.error('❌ No topics configured in topics.txt');
      process.exit(1);
    }

    // Step 2: Fetch all RSS feeds
    console.log('🔍 Fetching RSS feeds...');
    const allItems = await feedParser.fetchAllFeeds(feedUrls);
    console.log(`Fetched ${allItems.length} total items`);

    // Step 3: Filter by timeframe
    console.log(`⏱️  Filtering items from last ${TIMEFRAME_HOURS} hours...`);
    const recentItems = feedParser.filterByTimeframe(allItems, TIMEFRAME_HOURS);
    console.log(`Found ${recentItems.length} recent items`);

    if (recentItems.length === 0) {
      console.log('✅ No new items to report');
      return;
    }

    // Step 4: Curate based on topics
    console.log('🔎 Curating content based on topics...');
    const curatedItems = curator.curateItems(recentItems, topics);
    console.log(`Curated ${curatedItems.length} relevant items`);

    if (curatedItems.length === 0) {
      console.log('✅ No relevant items found');
      return;
    }

    // Step 5: Generate summaries
    console.log('✍️  Generating AI summaries...');
    const itemsWithSummaries = await summarizer.summarizeBatch(curatedItems, topics);

    // Step 6: Generate digest
    console.log('📝 Generating digest...');
    const digest = await summarizer.generateDigest(itemsWithSummaries, topics);

    // Step 7: Post to Slack
    console.log('📤 Posting to Slack...');
    await slackPoster.postCompleteDigest(SLACK_CHANNEL, digest, itemsWithSummaries);

    console.log('✅ WellRead Bot completed successfully!');
  } catch (error) {
    console.error('❌ Error:', error.message);
    console.error(error.stack);
    process.exit(1);
  }
}

main();
