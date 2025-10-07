# WellRead Bot 📰🤖

An intelligent RSS feed monitoring Slackbot that curates and summarizes content based on your interests, powered by Claude AI.

## Features

- 📡 **RSS Feed Monitoring**: Monitors multiple RSS feeds from a configurable text file
- ⏰ **Configurable Timeframe**: Aggregates posts over a customizable period (default: 24 hours)
- 🎯 **Semantic Curation**: Uses OpenAI embeddings to find content semantically similar to your topics of interest
- 🔢 **Configurable Limits**: Set maximum number of articles to surface (default: 20, ordered by relevance)
- ✍️ **AI Summaries**: Uses Claude to generate concise, insightful summaries for each item
- 💬 **Threaded Slack Posts**: Posts a daily digest, with each paper in its own thread containing an AI summary
- 🤖 **GitHub Actions**: Runs automatically on schedule via GitHub Actions

## Setup

### 1. Clone and Install

First, install [uv](https://docs.astral.sh/uv/getting-started/installation/) if you haven't already:

```bash
# On macOS and Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# On Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Then clone and install dependencies:

```bash
git clone <your-repo-url>
cd wellread
uv sync
```

### 2. Install Git Hooks (Optional but Recommended)

Install the pre-commit hook to prevent committing debug code:

```bash
./install-hooks.sh
```

This hook prevents committing any lines containing `NOCOMMIT`, which is useful for temporary debugging changes.

### 3. Configure RSS Feeds

Edit `feeds.txt` and add your RSS feed URLs (one per line):

```
https://arxiv.org/rss/cs.AI
https://arxiv.org/rss/cs.LG
https://blog.example.com/feed
```

### 4. Configure Topics

Edit `topics.txt` and add your topics of interest (one per line):

```
machine learning
large language models
neural networks
artificial intelligence
```

### 5. Configure Settings (Optional)

Edit `config.json` to adjust settings:

```json
{
  "timeframe_hours": 24,
  "max_items": 20
}
```

- `timeframe_hours`: How far back to look for new posts (default: 24)
- `max_items`: Maximum number of articles to surface, ordered by semantic relevance (default: 20)

### 6. Set Up Slack

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

### 7. Get OpenAI API Key

1. Go to https://platform.openai.com/api-keys
2. Create a new API key
3. Copy the key (starts with `sk-`)

**Note**: The bot uses `text-embedding-3-small` for semantic similarity. Cost is ~$0.02 per 1M tokens.

### 8. Get Anthropic API Key

1. Go to https://console.anthropic.com/
2. Create an API key
3. Copy the key (starts with `sk-ant-`)

### 9. Configure GitHub Secrets

In your GitHub repository, go to Settings → Secrets and variables → Actions, and add:

- `OPENAI_API_KEY`: Your OpenAI API key (required for semantic curation)
- `ANTHROPIC_API_KEY`: Your Anthropic API key (required for summaries)
- `SLACK_BOT_TOKEN`: Your Slack bot token (xoxb-...)
- `SLACK_CHANNEL`: Your Slack channel ID (e.g., C01234ABCD)
- `SLACK_WEBHOOK`: (Optional) Slack webhook URL
- `TIMEFRAME_HOURS`: (Optional) Override default timeframe (e.g., 48)
- `MAX_ITEMS`: (Optional) Override maximum items to surface (e.g., 10)

### 10. Configure Schedule

Edit `.github/workflows/daily-digest.yml` to change the schedule:

```yaml
on:
  schedule:
    - cron: '0 9 * * *'  # 9 AM UTC daily
```

## Manual Testing

Run locally with environment variables:

```bash
export OPENAI_API_KEY="your-openai-key"
export ANTHROPIC_API_KEY="your-anthropic-key"
export SLACK_BOT_TOKEN="your-token"
export SLACK_CHANNEL="your-channel-id"
uv run python src/main.py
```

Or trigger manually in GitHub Actions:
1. Go to Actions tab
2. Select "Daily RSS Digest"
3. Click "Run workflow"

## How It Works

1. **Fetch**: Retrieves items from all RSS feeds in `feeds.txt`
2. **Filter**: Keeps only items from the configured timeframe
3. **Curate**: Uses OpenAI embeddings to calculate semantic similarity between article titles and topics in `topics.txt`, then ranks by relevance and limits to top N items
4. **Summarize**: Uses Claude to generate summaries for curated items
5. **Post**: Creates a Slack digest with each paper in a thread containing its summary

## Project Structure

```
wellread/
├── src/
│   ├── main.py            # Main entry point
│   ├── rss_parser.py      # RSS feed fetching and parsing
│   ├── curator.py         # Content curation logic
│   ├── summarizer.py      # Claude AI integration
│   └── slack_poster.py    # Slack posting with threading
├── .github/
│   └── workflows/
│       └── daily-digest.yml  # GitHub Actions workflow
├── feeds.txt              # RSS feed URLs
├── topics.txt             # Topics of interest
├── config.json            # Configuration
├── pyproject.toml         # Project metadata and dependencies
└── uv.lock                # Locked dependencies (auto-generated)
```

## Customization

### Adjust Curation Parameters

Edit `config.json` or use environment variables:

- `max_items`: Change how many articles to surface
- `timeframe_hours`: Adjust lookback period

To change the embedding model or similarity calculation, edit `src/curator.py`:

```python
def __init__(self, openai_api_key: str):
    self.embedding_model = "text-embedding-3-small"  # or "text-embedding-3-large"
```

### Change Summary Style

Edit `src/summarizer.py` to modify the Claude prompt:

```python
async def summarize_paper(self, item, topics):
    prompt = """Your custom prompt here..."""
    # ...
```

### Modify Slack Format

Edit `src/slack_poster.py` to change message formatting:

```python
async def post_paper_with_summary(self, channel, thread_ts, paper, index, total):
    # Customize Slack message blocks here
    pass
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
- Adjust `max_concurrent` parameter in `src/summarizer.py`
- Add delays between API calls if needed

## License

MIT
