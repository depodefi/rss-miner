# RSS Miner
RSS Feeds from various AI blogs.

## Usage
Run `python3 run_feeds.py` to generate all feeds.

## Available Scrapers
- **Anthropic**: Fetches blog posts from `anthropic.com/news` (last 60 days).
- **ElevenLabs**: Fetches blog posts from `elevenlabs.io/blog` (last 60 days).
- **NVIDIA**: Fetches blog posts from `blogs.nvidia.com` (last 60 days).
- **Google AI**: Fetches blog posts from `blog.google/technology/ai` (last 60 days).
- **AMD**: Fetches press releases from `ir.amd.com` (last 60 days).
- **Perplexity**: Fetches blog posts from `perplexity.ai/hub` (last 60 days).
- **Palantir**: Fetches press releases from `palantir.com` (last 60 days).
- **Amazon AI**: Fetches AI news from `aboutamazon.com` (last 60 days).

## Output
Feeds are generated in the `feed/` directory.
