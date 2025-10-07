import { WebClient } from '@slack/web-api';

export class SlackPoster {
  constructor(token, webhook) {
    this.client = new WebClient(token);
    this.webhook = webhook;
  }

  async postDigest(channel, digest, itemCount) {
    const message = {
      channel: channel,
      text: `📰 *Daily Research Digest* - ${new Date().toLocaleDateString()}`,
      blocks: [
        {
          type: 'header',
          text: {
            type: 'plain_text',
            text: `📰 Daily Research Digest - ${new Date().toLocaleDateString()}`
          }
        },
        {
          type: 'section',
          text: {
            type: 'mrkdwn',
            text: digest
          }
        },
        {
          type: 'context',
          elements: [
            {
              type: 'mrkdwn',
              text: `Found *${itemCount}* relevant items. Individual summaries below 👇`
            }
          ]
        }
      ]
    };

    try {
      const result = await this.client.chat.postMessage(message);
      return result.ts; // Return the timestamp for threading
    } catch (error) {
      console.error('Error posting digest:', error.message);
      throw error;
    }
  }

  async postPaperWithSummary(channel, threadTs, paper, index, total) {
    try {
      // Post the main paper info
      const paperMessage = {
        channel: channel,
        thread_ts: threadTs,
        text: paper.title,
        blocks: [
          {
            type: 'section',
            text: {
              type: 'mrkdwn',
              text: `*${index}/${total}: ${paper.title}*\n\n${paper.description ? paper.description.substring(0, 300) + (paper.description.length > 300 ? '...' : '') : 'No description available'}`
            }
          },
          {
            type: 'section',
            fields: [
              {
                type: 'mrkdwn',
                text: `*Source:*\n${paper.feedSource}`
              },
              {
                type: 'mrkdwn',
                text: `*Published:*\n${new Date(paper.pubDate).toLocaleDateString()}`
              }
            ]
          },
          {
            type: 'section',
            text: {
              type: 'mrkdwn',
              text: `🔗 <${paper.link}|Read more>`
            }
          }
        ]
      };

      const paperResult = await this.client.chat.postMessage(paperMessage);

      // Small delay between messages
      await new Promise(resolve => setTimeout(resolve, 500));

      // Post the summary as a reply in the thread
      const summaryMessage = {
        channel: channel,
        thread_ts: paperResult.ts, // Thread off the paper post
        text: `📝 Summary: ${paper.summary}`,
        blocks: [
          {
            type: 'section',
            text: {
              type: 'mrkdwn',
              text: `📝 *AI Summary*\n\n${paper.summary}`
            }
          }
        ]
      };

      await this.client.chat.postMessage(summaryMessage);

      return paperResult.ts;
    } catch (error) {
      console.error(`Error posting paper "${paper.title}":`, error.message);
      throw error;
    }
  }

  async postAllPapers(channel, digestTs, papers) {
    const total = papers.length;

    for (let i = 0; i < papers.length; i++) {
      await this.postPaperWithSummary(channel, digestTs, papers[i], i + 1, total);

      // Rate limiting between papers
      if (i < papers.length - 1) {
        await new Promise(resolve => setTimeout(resolve, 1000));
      }
    }
  }

  async postCompleteDigest(channel, digest, papers) {
    console.log(`Posting digest to channel ${channel}...`);

    // Post the main digest
    const digestTs = await this.postDigest(channel, digest, papers.length);

    console.log(`Digest posted. Now posting ${papers.length} individual papers...`);

    // Post each paper with its summary
    await this.postAllPapers(channel, digestTs, papers);

    console.log('All papers posted successfully!');
  }
}
