import Anthropic from '@anthropic-ai/sdk';

export class ClaudeSummarizer {
  constructor(apiKey) {
    this.client = new Anthropic({
      apiKey: apiKey
    });
  }

  async summarizePaper(item, topics) {
    const prompt = `You are analyzing an RSS feed item for a research digest. Here are the details:

Title: ${item.title}
Source: ${item.feedSource}
${item.creator ? `Author: ${item.creator}` : ''}

Content:
${item.description || item.content || 'No content available'}

Topics of interest: ${topics.join(', ')}

Please provide a concise, insightful summary (2-4 sentences) that:
1. Explains the main contribution or finding
2. Highlights why it's relevant to the topics of interest
3. Notes any practical implications or applications

Keep the tone professional but engaging.`;

    try {
      const message = await this.client.messages.create({
        model: 'claude-3-5-sonnet-20241022',
        max_tokens: 300,
        messages: [{
          role: 'user',
          content: prompt
        }]
      });

      return message.content[0].text;
    } catch (error) {
      console.error(`Error summarizing item "${item.title}":`, error.message);
      return `Summary unavailable: ${error.message}`;
    }
  }

  async summarizeBatch(items, topics, maxConcurrent = 3) {
    const results = [];

    for (let i = 0; i < items.length; i += maxConcurrent) {
      const batch = items.slice(i, i + maxConcurrent);
      const summaries = await Promise.all(
        batch.map(item => this.summarizePaper(item, topics))
      );

      batch.forEach((item, idx) => {
        results.push({
          ...item,
          summary: summaries[idx]
        });
      });

      // Rate limiting: wait a bit between batches
      if (i + maxConcurrent < items.length) {
        await new Promise(resolve => setTimeout(resolve, 1000));
      }
    }

    return results;
  }

  async generateDigest(items, topics) {
    const itemsList = items.slice(0, 20).map((item, idx) =>
      `${idx + 1}. ${item.title} (${item.feedSource})`
    ).join('\n');

    const prompt = `Create a brief digest summary (3-4 sentences) for today's research roundup. Here are the curated items:

${itemsList}

Topics of focus: ${topics.join(', ')}

Provide an engaging overview that highlights key themes and noteworthy developments.`;

    try {
      const message = await this.client.messages.create({
        model: 'claude-3-5-sonnet-20241022',
        max_tokens: 250,
        messages: [{
          role: 'user',
          content: prompt
        }]
      });

      return message.content[0].text;
    } catch (error) {
      console.error('Error generating digest:', error.message);
      return `Found ${items.length} relevant items from your RSS feeds.`;
    }
  }
}
