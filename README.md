# WellRead Bot 📰🤖

An intelligent RSS feed monitoring Slackbot that curates and summarizes content based on your interests, powered by Claude AI.

## Features

- 📡 **RSS Feed Monitoring**: Monitors multiple RSS feeds from a configurable text file
- ⏰ **Configurable Timeframe**: Aggregates posts over a customizable period (default: 24 hours)
- 🎯 **Smart Curation**: Filters content based on topics and interests specified in a text file
- ✍️ **AI Summaries**: Uses Claude to generate concise, insightful summaries for each item
- 💬 **Threaded Slack Posts**: Posts a daily digest, with each paper in its own thread containing an AI summary
- 🤖 **GitHub Actions**: Runs automatically on schedule via GitHub Actions

## Setup

### 1. Clone and Install

```bash
git clone <your-repo-url>
cd wellread
npm install
```

### 2. Configure RSS Feeds

Edit `feeds.txt` and add your RSS feed URLs (one per line):

```
https://arxiv.org/rss/cs.AI
https://arxiv.org/rss/cs.LG
https://blog.example.com/feed
```

### 3. Configure Topics

Edit `topics.txt` and add your topics of interest (one per line):

```
machine learning
large language models
neural networks
artificial intelligence
```

### 4. Configure Timeframe (Optional)

Edit `config.json` to adjust the timeframe:

```json
{
  "timeframe_hours": 24
}
```

### 5. Set Up Slack

#### Create a Slack App

1. Go to https://api.slack.com/apps
2. Click "Create New App" → "From scratch"
3. Name it "WellRead Bot" and select your workspace

#### Configure Bot Token Scopes

Under "OAuth & Permissions", add these scopes:
- `chat:write`
- `chat:write.public`
- `channels:read`
- `groups:read`

#### Install to Workspace

1. Click "Install to Workspace"
2. Copy the "Bot User OAuth Token" (starts with `xoxb-`)

#### Get Channel ID

In Slack, right-click your target channel → "View channel details" → Copy the Channel ID at the bottom

### 6. Get Anthropic API Key

1. Go to https://console.anthropic.com/
2. Create an API key
3. Copy the key (starts with `sk-ant-`)

### 7. Configure GitHub Secrets

In your GitHub repository, go to Settings → Secrets and variables → Actions, and add:

- `ANTHROPIC_API_KEY`: Your Anthropic API key
- `SLACK_BOT_TOKEN`: Your Slack bot token (xoxb-...)
- `SLACK_CHANNEL`: Your Slack channel ID (e.g., C01234ABCD)
- `SLACK_WEBHOOK`: (Optional) Slack webhook URL
- `TIMEFRAME_HOURS`: (Optional) Override default timeframe (e.g., 48)

### 8. Configure Schedule

Edit `.github/workflows/daily-digest.yml` to change the schedule:

```yaml
on:
  schedule:
    - cron: '0 9 * * *'  # 9 AM UTC daily
```

## Manual Testing

Run locally with environment variables:

```bash
export ANTHROPIC_API_KEY="your-key"
export SLACK_BOT_TOKEN="your-token"
export SLACK_CHANNEL="your-channel-id"
npm start
```

Or trigger manually in GitHub Actions:
1. Go to Actions tab
2. Select "Daily RSS Digest"
3. Click "Run workflow"

## How It Works

1. **Fetch**: Retrieves items from all RSS feeds in `feeds.txt`
2. **Filter**: Keeps only items from the configured timeframe
3. **Curate**: Scores items based on relevance to topics in `topics.txt`
4. **Summarize**: Uses Claude to generate summaries for curated items
5. **Post**: Creates a Slack digest with each paper in a thread containing its summary

## Project Structure

```
wellread/
├── src/
│   ├── index.js           # Main entry point
│   ├── rss-parser.js      # RSS feed fetching and parsing
│   ├── curator.js         # Content curation logic
│   ├── summarizer.js      # Claude AI integration
│   └── slack-poster.js    # Slack posting with threading
├── .github/
│   └── workflows/
│       └── daily-digest.yml  # GitHub Actions workflow
├── feeds.txt              # RSS feed URLs
├── topics.txt             # Topics of interest
├── config.json            # Configuration
└── package.json
```

## Customization

### Adjust Curation Sensitivity

Edit `src/curator.js` to modify the scoring algorithm:

```javascript
calculateRelevanceScore(item, topics) {
  // Customize scoring logic here
}
```

### Change Summary Style

Edit `src/summarizer.js` to modify the Claude prompt:

```javascript
async summarizePaper(item, topics) {
  const prompt = `Your custom prompt here...`;
  // ...
}
```

### Modify Slack Format

Edit `src/slack-poster.js` to change message formatting:

```javascript
async postPaperWithSummary(channel, threadTs, paper, index, total) {
  // Customize Slack message blocks here
}
```

## Troubleshooting

### No items found
- Check that feeds in `feeds.txt` are valid RSS/Atom feeds
- Verify the timeframe isn't too restrictive
- Ensure topics in `topics.txt` match content in feeds

### Slack posting fails
- Verify bot token has correct permissions
- Check that channel ID is correct
- Ensure bot is added to the channel

### Rate limiting
- Adjust `maxConcurrent` in `src/summarizer.js`
- Add delays between API calls if needed

## License

MIT
