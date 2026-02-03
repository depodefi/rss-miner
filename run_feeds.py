import os
import importlib.util
import sys
from scrapers.elevenlabs import ElevenLabsScraper
from scrapers.amazon import AmazonScraper
from scrapers.palantir import PalantirScraper
from scrapers.anthropic import AnthropicScraper
from scrapers.perplexity import PerplexityScraper
from scrapers.amd import AMDScraper
from scrapers.google_ai import GoogleAIScraper
from scrapers.nvidia import NvidiaScraper
from scrapers.openai import OpenAIScraper
from scrapers.reallysimpleai import ReallySimpleAIScraper

def run_scrapers():
    # The original code dynamically discovers scrapers in a directory.
    # The instruction implies a change to an explicit list of modules.
    # This change replaces the directory scanning logic with a fixed list.
    scrapers = [
        OpenAIScraper(),
        NvidiaScraper(),
        GoogleAIScraper(),
        AMDScraper(),
        PerplexityScraper(),
        PalantirScraper(),
        AmazonScraper(),
        ElevenLabsScraper(),
        AnthropicScraper(),
        ReallySimpleAIScraper()
    ]

    print(f"Running specific scrapers: {[s.__class__.__name__ for s in scrapers]}...")

    # Get disabled scrapers from environment variable
    disabled_env = os.environ.get("DISABLED_SCRAPERS", "")
    disabled_scrapers = [s.strip() for s in disabled_env.split(",") if s.strip()]
    if disabled_scrapers:
        print(f"Disabled scrapers: {disabled_scrapers}")
    
    success = True
    for scraper in scrapers:
        name = scraper.__class__.__name__
        
        if name in disabled_scrapers:
            print(f"Skipping scraper: {name} (Disabled via config)")
            print("-" * 20)
            continue

        print(f"Running scraper: {name}")
        
        try:
            if hasattr(scraper, "generate_feed") and callable(scraper.generate_feed):
                scraper.generate_feed()
                print(f"Successfully ran {name}")
            else:
                print(f"Skipping {name}: No 'generate_feed' method found.")
        except Exception as e:
            print(f"Error running {name}: {e}")
            success = False
        print("-" * 20)

    if not success:
        print("One or more scrapers failed.")
        sys.exit(1)

    generate_index_html()

def generate_index_html():
    """Generates an index.html linking to all XML feeds."""
    feed_dir = "feed"
    if not os.path.exists(feed_dir):
        return

    files = [f for f in os.listdir(feed_dir) if f.endswith(".xml")]
    files.sort()

    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>RSS Feeds</title>
        <style>
            body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; max-width: 800px; margin: 40px auto; padding: 0 20px; line-height: 1.6; }
            h1 { border-bottom: 2px solid #eaecef; padding-bottom: 0.3em; }
            ul { list-style-type: none; padding: 0; }
            li { padding: 10px 0; border-bottom: 1px solid #eaecef; }
            a { text-decoration: none; color: #0366d6; font-weight: 600; font-size: 1.1em; }
            a:hover { text-decoration: underline; }
            .meta { color: #6a737d; font-size: 0.9em; margin-left: 10px; }
        </style>
    </head>
    <body>
        <h1>Available RSS Feeds</h1>
        <ul>
    """

    for f in files:
        file_path = os.path.join(feed_dir, f)
        size_kb = os.path.getsize(file_path) / 1024
        html_content += f'            <li><a href="{f}">{f}</a> <span class="meta">({size_kb:.1f} KB)</span></li>\n'

    html_content += """
        </ul>
    </body>
    </html>
    """

    with open(os.path.join(feed_dir, "index.html"), "w") as f:
        f.write(html_content)
    print("Generated feed/index.html")

if __name__ == "__main__":
    run_scrapers()
