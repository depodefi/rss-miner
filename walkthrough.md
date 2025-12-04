# Perplexity Scraper Implementation Walkthrough

## Objective
Develop a scraper for Perplexity AI Hub (`https://www.perplexity.ai/hub`) to generate an RSS feed with full article content.

## Challenges
1.  **Cloudflare Protection**: The hub page and article pages are protected by Cloudflare, preventing direct access with standard `requests`.
2.  **Dynamic Content**: The site uses Framer, which renders content dynamically.
3.  **Duplicate Content**: The HTML contains multiple versions of the article text for responsive design (desktop, mobile, etc.).

## Solution

### 1. Cloudflare Bypass
We used the `cloudscraper` library to bypass Cloudflare protection. This allows us to fetch the full HTML content of the hub and article pages.

### 2. Article Discovery
We parse the main hub page (`https://www.perplexity.ai/hub`) to find links to blog posts. These links follow the pattern `/hub/blog/...`.

### 3. Content Extraction
To extract the full article content:
- We identify paragraphs with the class `framer-text`.
- We filter for paragraphs that look like body content (length > 100 characters).
- We find the parent container of the first matching paragraph.
- We extract all text from this parent container, which ensures we get the full article without duplicates from other responsive variants.
- We clean the text by removing metadata prefixes (e.g., "Written by...") and flattening it to a single line.

### 4. RSS Generation
- We use the `rfeed` library to generate the RSS feed.
- The feed is saved to `feed/perplexity.xml`.
- Descriptions are wrapped in `<![CDATA[...]]>` to preserve formatting (though we flatten to text).
- Publication dates are extracted from the `application/ld+json` script tag in the article HTML.
- **Sorting**: Articles are sorted by publication date (newest first).
- **Filtering**: Only articles from the last 60 days are included.
- **Formatting**: The XML output is pretty-printed for readability.

### 5. Palantir Scraper
- **Source**: `https://www.palantir.com/newsroom/press-releases/`
- **Method**: Parses `__NEXT_DATA__` JSON embedded in the HTML.
- **Content**: Extracts metadata (headline, date, link). Content is the headline as press releases link to external sites.
- **Sorting**: Articles are sorted by publication date (newest first).
- **Filtering**: Only articles from the last 60 days are included.
- **Output**: `feed/palantir.xml`

### 6. ElevenLabs Scraper
- **Source**: `https://elevenlabs.io/blog`
- **Logic**:
  - Fetches the main blog page to find article links.
  - Fetches each article page to extract the full content and precise publication date.
  - **Date Parsing**: Uses the `datetime` attribute from the `<time>` tag on the article page.
  - **Content Extraction**: Extracts text from `div.rich-text-blog` or `article`, flattening it to a single line.
  - **Filtering**: Keeps articles from the last 60 days.
  - **Output**: `feed/elevenlabs.xml` with CDATA-wrapped descriptions.

### 7. Amazon Scraper
- **Source**: `https://www.aboutamazon.com/artificial-intelligence-ai-news`
- **Logic**:
  - Fetches the main news page.
  - Extracts article cards (`div.promo-card-v2--articlerouting`).
  - Fetches full content from individual article pages (`div.ArticlePage-articleBody`).
  - Cleans text to be single-line and wraps in CDATA.
  - Filters articles older than 60 days.
  - **Output**: `feed/amazon.xml`.

## Integration
The scrapers are implemented in `scrapers/` and are automatically picked up by `run_feeds.py`.

## Usage
Run the following command to generate all feeds, including Perplexity:
```bash
python3 run_feeds.py
```
