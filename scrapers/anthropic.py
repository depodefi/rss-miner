import requests
from bs4 import BeautifulSoup
from rfeed import *
import datetime
from email.utils import formatdate
import re
import xml.dom.minidom
import os

class AnthropicScraper:
    def generate_feed(self):
        url = "https://www.anthropic.com/news"
        try:
            response = requests.get(url)
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"Error fetching URL: {e}")
            return

        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find all news items
        # Selector: a[href^="/news/"]
        articles = soup.select('a[href^="/news/"]')
        
        items = []
        seen_guids = set()
        
        for article in articles:
            # Link
            link = article.get('href')
            if link.startswith('/'):
                link = f"https://www.anthropic.com{link}"
                
            if link in seen_guids:
                continue
            seen_guids.add(link)
                
            # Title
            # Try h2, h3, h4, h5
            title_tag = article.find(['h2', 'h3', 'h4', 'h5'])
            if not title_tag:
                # Fallback for list items: look for span with class containing 'title'
                title_tag = article.find('span', class_=lambda x: x and 'title' in x.lower())

            title = title_tag.get_text(strip=True) if title_tag else "No Title"

            # Date
            # Look for time tag
            pub_date = datetime.datetime.now() # Default to now
            date_str = ""

            time_tag = article.find('time')
            if time_tag:
                text = time_tag.get_text(strip=True)
                # Example: Nov 24, 2025
                formats = [
                    "%b %d, %Y",
                    "%B %d, %Y",
                    "%Y-%m-%d"
                ]
                for fmt in formats:
                    try:
                        pub_date = datetime.datetime.strptime(text, fmt)
                        date_str = text
                        break
                    except ValueError:
                        continue

            # Description
            # Find the first p tag
            description_tag = article.find('p')
            description = description_tag.get_text(strip=True) if description_tag else ""

            # Check if description is missing or generic
            is_generic = description.startswith("Anthropic is an AI safety and research company")

            if not description or is_generic:
                try:
                    print(f"Fetching description for: {link}")
                    art_response = requests.get(link)
                    art_response.raise_for_status()
                    art_soup = BeautifulSoup(art_response.content, 'html.parser')

                    new_description = ""

                    # Try meta description
                    meta_desc = art_soup.find('meta', attrs={'name': 'description'})
                    if meta_desc:
                        content = meta_desc.get('content', '')
                        if content and not content.startswith("Anthropic is an AI safety and research company"):
                            new_description = content

                    # Try og:description
                    if not new_description:
                        og_desc = art_soup.find('meta', attrs={'property': 'og:description'})
                        if og_desc:
                            content = og_desc.get('content', '')
                            if content and not content.startswith("Anthropic is an AI safety and research company"):
                                new_description = content

                    # Fallback to full article content
                    if not new_description:
                        main_content = art_soup.find('main')
                        if main_content:
                            paragraphs = main_content.find_all('p')
                            if paragraphs:
                                # Take all paragraphs and join with space for single line
                                text_chunks = [p.get_text(strip=True) for p in paragraphs]
                                new_description = " ".join(text_chunks)

                    if new_description:
                        description = new_description

                except Exception as e:
                    print(f"Failed to fetch description for {link}: {e}")

            # Filter out items older than 2 months (approx 60 days)
            cutoff_date = datetime.datetime.now() - datetime.timedelta(days=60)
            if pub_date < cutoff_date:
                continue

            item = Item(
                title=title,
                link=link,
                description=description,
                author="Anthropic",
                guid=Guid(link),
                pubDate=pub_date
            )
            items.append(item)
        
        # Sort items by pubDate descending (newest first)
        items.sort(key=lambda x: x.pubDate, reverse=True)
        
        feed = Feed(
            title="Anthropic News",
            link="https://www.anthropic.com/news",
            description="Latest news from Anthropic",
            language="en-US",
            lastBuildDate=datetime.datetime.now(),
            items=items
        )

        rss_content = feed.rss()
        dom = xml.dom.minidom.parseString(rss_content)
        pretty_xml = dom.toprettyxml(indent="  ")

        os.makedirs("feed", exist_ok=True)

        with open("feed/anthropic.xml", "w") as f:
            f.write(pretty_xml)
        print(f"Generated feed/anthropic.xml with {len(items)} items.")

if __name__ == "__main__":
    scraper = AnthropicScraper()
    scraper.generate_feed()
