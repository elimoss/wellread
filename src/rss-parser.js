import Parser from 'rss-parser';
import fs from 'fs/promises';

export class RSSFeedParser {
  constructor() {
    this.parser = new Parser({
      customFields: {
        item: [
          ['dc:creator', 'creator'],
          ['content:encoded', 'contentEncoded']
        ]
      }
    });
  }

  async loadFeeds(feedsFile = 'feeds.txt') {
    const content = await fs.readFile(feedsFile, 'utf-8');
    return content
      .split('\n')
      .map(line => line.trim())
      .filter(line => line && !line.startsWith('#'));
  }

  async fetchFeed(url) {
    try {
      const feed = await this.parser.parseURL(url);
      return {
        success: true,
        feedTitle: feed.title,
        items: feed.items.map(item => ({
          title: item.title,
          link: item.link,
          pubDate: item.pubDate,
          creator: item.creator || item.author,
          description: item.contentSnippet || item.description,
          content: item.contentEncoded || item.content,
          feedSource: feed.title
        }))
      };
    } catch (error) {
      console.error(`Error fetching feed ${url}:`, error.message);
      return {
        success: false,
        error: error.message
      };
    }
  }

  async fetchAllFeeds(feedUrls) {
    const results = await Promise.all(
      feedUrls.map(url => this.fetchFeed(url))
    );

    const allItems = results
      .filter(result => result.success)
      .flatMap(result => result.items);

    return allItems;
  }

  filterByTimeframe(items, hoursAgo = 24) {
    const cutoffTime = new Date(Date.now() - hoursAgo * 60 * 60 * 1000);

    return items.filter(item => {
      if (!item.pubDate) return false;
      const pubDate = new Date(item.pubDate);
      return pubDate > cutoffTime;
    });
  }
}
