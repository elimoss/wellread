# WellRead Bot 📰🤖

An intelligent RSS feed monitoring Slackbot that curates and summarizes content based on your interests, powered by Claude AI.

## Features

- 📡 **RSS Feed Monitoring**: Monitors multiple RSS feeds from a configurable text file
- ⏰ **Configurable Timeframe**: Aggregates posts over a customizable period (default: 24 hours)
- 🎯 **Semantic Curation**: Uses OpenAI embeddings to find content semantically similar to your topics of interest
- 🔢 **Configurable Limits**: Set maximum number of articles to post (default: 20, ordered by relevance)
- ✍️ **AI Summaries**: Uses Claude to generate concise, insightful summaries for each item
- 💬 **Clean Slack Layout**: Each paper posted as a top-level message with AI summary in thread; digest summary posted at the end
- 🤖 **GitHub Actions**: Runs automatically on schedule via GitHub Actions

## Getting Started

### Fork This Repository

**Important:** You should fork this repository to your own GitHub account rather than cloning it directly. This allows:

- GitHub Actions to run automatically on your schedule
- Persistent embedding cache across workflow runs
- Easy customization and updates specific to your needs

**To fork:**
1. Click the "Fork" button at the top right of this repository
2. Select your GitHub account as the destination
3. GitHub will create a copy of this repository under your account

Once forked, you can clone your fork and configure it following the setup instructions below.

## Setup

### 1. Clone Your Fork and Install

First, install [uv](https://docs.astral.sh/uv/getting-started/installation/) if you haven't already:

```bash
# On macOS and Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# On Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Then clone your forked repository and install dependencies:

```bash
git clone https://github.com/YOUR-USERNAME/wellread.git
cd wellread
uv sync
```

Replace `YOUR-USERNAME` with your GitHub username.

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
  "max_items_to_post": 20,
  "min_relevance_score": 0.1,
  "cache_posted_articles": true,
  "posted_articles_cache_file": "cache/posted_articles.json",
  "embedding_cache_dir": "cache/embeddings",
  "llm_models": {
    "summarization": "claude-sonnet-4-5-20250929",
    "digest": "claude-sonnet-4-5-20250929"
  }
}
```

- `timeframe_hours`: How far back to look for new posts (default: 24)
- `max_items_to_post`: Maximum number of articles to post (default: 20)
- `min_relevance_score`: Minimum semantic similarity score (0-100) for articles to be included (default: 0.1)
- `cache_posted_articles`: Whether to cache posted articles to avoid reposting (default: true)
- `posted_articles_cache_file`: File path for the posted articles cache (default: cache/posted_articles.json)
- `embedding_cache_dir`: Directory for caching OpenAI embeddings (default: cache/embeddings)
- `llm_models.summarization`: Claude model for individual article summaries (default: claude-sonnet-4-5-20250929)
- `llm_models.digest`: Claude model for overall digest (default: claude-sonnet-4-5-20250929)

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

**Note**: The bot uses `text-embedding-3-small` for semantic similarity. Cost is ~$0.02 per 1M tokens. Embeddings are cached locally and in GitHub Actions to minimize API calls.

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
- `MAX_ITEMS_TO_POST`: (Optional) Override maximum items to post (e.g., 10)

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
2. **Deduplicate**: Removes duplicate articles within the current run (based on URL)
3. **Filter by Time**: Keeps only items from the configured timeframe
4. **Filter Previously Posted**: Removes articles that have been posted before (if caching enabled)
5. **Curate**: Uses OpenAI embeddings to calculate semantic similarity between article titles and topics in `topics.txt`, then ranks by relevance and limits to top N items
6. **Summarize**: Uses Claude to generate summaries for curated items
7. **Post**: Posts header, then each paper as a top-level Slack message with summary, then digest summary at the end
8. **Cache**: Saves posted article URLs to prevent reposting

## Project Structure

```
wellread/
├── src/
│   ├── main.py            # Main entry point
│   ├── rss_parser.py      # RSS feed fetching and parsing
│   ├── curator.py         # Content curation logic
│   ├── summarizer.py      # Claude AI integration
│   ├── slack_poster.py    # Slack posting with threading
│   └── article_cache.py   # Posted articles cache management
├── .github/
│   └── workflows/
│       └── daily-digest.yml  # GitHub Actions workflow
├── feeds.txt              # RSS feed URLs
├── topics.txt             # Topics of interest
├── config.json            # Configuration
├── pyproject.toml         # Project metadata and dependencies
├── uv.lock                # Locked dependencies (auto-generated)
└── cache/
    ├── embeddings/        # OpenAI embeddings cache (gitignored)
    └── posted_articles.json  # Posted articles cache (gitignored)
```

## Caching

The bot uses two types of caching to optimize performance and avoid reposting:

### OpenAI Embeddings Cache

Automatically caches OpenAI embeddings to minimize API costs:

- **Local Development**: Cache stored in `cache/embeddings/` (gitignored)
- **GitHub Actions**: Cache persists across workflow runs (expires after 7 days of inactivity)
- **Cache Key**: Embeddings are keyed by `model:text_hash` to handle model upgrades
- **Benefits**: Topics are typically cached permanently; recurring articles skip re-embedding

View cache stats in the bot output:
```
Topic embeddings: 6 cached, 0 new
Article embeddings: 42 cached, 8 new
Total API calls saved: 48
```

### Posted Articles Cache

Tracks previously posted articles to avoid reposting (enabled by default):

- **Local Development**: Cache stored in `cache/posted_articles.json` (gitignored)
- **GitHub Actions**: Cache persists across all workflow runs
- **Cache Key**: Article URLs are stored in a JSON file
- **Benefits**: Prevents duplicate posts even across multiple runs
- **Configuration**: Can be disabled by setting `cache_posted_articles: false` in `config.json`

When enabled, the bot logs:
```
📚 Loaded article cache with 47 previously posted articles
🔍 Filtering out previously posted articles...
15 unposted items (3 already posted)
```

## Customization

### Adjust Model Selection

Edit `config.json` to change Claude models:

```json
{
  "llm_models": {
    "summarization": "claude-3-5-haiku-20241022",  // Faster, cheaper
    "digest": "claude-sonnet-4-5-20250929"         // Higher quality
  }
}
```

Available models:
- `claude-sonnet-4-5-20250929` - Best quality (default)
- `claude-3-5-sonnet-20241022` - Good balance
- `claude-3-5-haiku-20241022` - Fast and cheap

Or use environment variables:
- `SUMMARIZATION_MODEL` - Override summarization model
- `DIGEST_MODEL` - Override digest model

### Adjust Curation Parameters

Edit `config.json` or use environment variables:

- `max_items_to_post`: Maximum number of articles to post (use `MAX_ITEMS_TO_POST` env var)
- `timeframe_hours`: Adjust lookback period (use `TIMEFRAME_HOURS` env var)
- `min_relevance_score`: Minimum relevance threshold (use `MIN_RELEVANCE_SCORE` env var)

To change the embedding model, edit `src/curator.py`:

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
