import os
import importlib.util
import sys
from scrapers.elevenlabs import ElevenLabsScraper
from scrapers.amazon import AmazonScraper
from scrapers.palantir import PalantirScraper
from scrapers.perplexity import PerplexityScraper
from scrapers.amd import AMDScraper
from scrapers.google_ai import GoogleAIScraper
from scrapers.nvidia import NvidiaScraper

def run_scrapers():
    # The original code dynamically discovers scrapers in a directory.
    # The instruction implies a change to an explicit list of modules.
    # This change replaces the directory scanning logic with a fixed list.
    scrapers = [
        NvidiaScraper(),
        GoogleAIScraper(),
        AMDScraper(),
        PerplexityScraper(),
        PalantirScraper(),
        AmazonScraper(),
        ElevenLabsScraper()
    ]

    print(f"Running specific scrapers: {[s.__class__.__name__ for s in scrapers]}...")
    
    for scraper in scrapers:
        name = scraper.__class__.__name__
        print(f"Running scraper: {name}")
        
        try:
            if hasattr(scraper, "generate_feed") and callable(scraper.generate_feed):
                scraper.generate_feed()
                print(f"Successfully ran {name}")
            else:
                print(f"Skipping {name}: No 'generate_feed' method found.")
        except Exception as e:
            print(f"Error running {name}: {e}")
        print("-" * 20)

if __name__ == "__main__":
    run_scrapers()
