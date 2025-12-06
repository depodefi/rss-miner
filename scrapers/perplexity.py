import requests
from bs4 import BeautifulSoup
import rfeed
from datetime import datetime, timedelta, timezone
import re
import cloudscraper
import json

import requests
from bs4 import BeautifulSoup
import rfeed
from datetime import datetime, timedelta, timezone
import re
import cloudscraper
import json

class PerplexityScraper:
    def extract_text(self, soup):
        # Find the first p.framer-text that looks like body content
        # We look for a paragraph with substantial length to avoid headers/footers
        paragraphs = soup.find_all('p', class_='framer-text')
        
        target_parent = None
        for p in paragraphs:
            text = p.get_text(strip=True)
            if len(text) > 100:
                target_parent = p.parent
                break
        
        if not target_parent:
            return ""
            
        # Extract text from the parent container
        full_text = target_parent.get_text(separator=' ', strip=True)
        
        # Clean up metadata if present at the start
        # Example: "Written by Perplexity Team Published on Dec 4, 2025 Perplexity x Cristiano Ronaldo ..."
        # We can try to remove the "Written by... Published on..." part
        
        # Remove "Written by..." up to a date pattern if possible, or just common prefixes
        full_text = re.sub(r'Written by.*?Published on.*?\d{4}', '', full_text, flags=re.IGNORECASE)
        
        # Remove title if it's repeated at the start (heuristic)
        title = soup.title.string if soup.title else ""
        if title:
            # Simple check if title is at the start
            clean_title = title.strip()
            if full_text.startswith(clean_title):
                full_text = full_text[len(clean_title):].strip()
                
        # Flatten to single line
        full_text = re.sub(r'\s+', ' ', full_text).strip()
        
        return full_text

    def generate_feed(self):
        scraper = cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'platform': 'windows',
                'desktop': True
            }
        )
        url = "https://www.perplexity.ai/hub"
        
        print(f"Fetching {url}...")
        response = scraper.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        articles = []
        links = set()
        
        # Extract article links
        for a in soup.find_all('a', href=True):
            href = a['href']
            if '/hub/blog/' in href:
                # Normalize URL
                if href.startswith('.'):
                    href = href[1:]
                if not href.startswith('http'):
                    href = f"https://www.perplexity.ai{href}"
                links.add(href)
                
        print(f"Found {len(links)} articles.")
        
        if len(links) == 0:
            print("WARNING: No articles found!")
            print(f"Response status code: {response.status_code}")
            print("Page title:", soup.title.string if soup.title else "No title")
            print("First 500 chars of HTML content:")
            print(response.text[:500])
            if "Just a moment" in response.text:
                print("POSSIBLE CLOUDFLARE BLOCK DETECTED")
        
        # Process articles (limit to 15 for now to avoid long runtimes/rate limits)
        for link in sorted(list(links))[:15]:
            print(f"Processing {link}...")
            try:
                art_response = scraper.get(link)
                art_soup = BeautifulSoup(art_response.text, 'html.parser')
                
                title = art_soup.title.string if art_soup.title else "No Title"
                
                # Extract date from JSON-LD
                pub_date = datetime.now(timezone.utc)
                json_ld = art_soup.find('script', type='application/ld+json')
                if json_ld:
                    try:
                        data = json.loads(json_ld.string)
                        if 'datePublished' in data:
                            pub_date = datetime.fromisoformat(data['datePublished'].replace('Z', '+00:00'))
                    except:
                        pass
                
                description = self.extract_text(art_soup)
                
                # Wrap description in CDATA
                description = f"<![CDATA[{description}]]>"
                
                item = rfeed.Item(
                    title=title,
                    link=link,
                    description=description,
                    pubDate=pub_date,
                    guid=rfeed.Guid(link)
                )
                articles.append(item)
                
            except Exception as e:
                print(f"Error processing {link}: {e}")
                continue
    
        # Sort articles by pubDate descending
        articles.sort(key=lambda x: x.pubDate, reverse=True)
        
        # Filter articles (last 2 months)
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=60)
        original_count = len(articles)
        articles = [a for a in articles if a.pubDate >= cutoff_date]
        print(f"Filtered {original_count - len(articles)} articles older than 60 days. Remaining: {len(articles)}")
    
        feed = rfeed.Feed(
            title="Perplexity AI Hub",
            link=url,
            description="Latest news and updates from Perplexity AI",
            language="en-US",
            lastBuildDate=datetime.now(),
            items=articles
        )
    
        xml_str = feed.rss()
        
        # Format XML
        try:
            from xml.dom import minidom
            dom = minidom.parseString(xml_str)
            pretty_xml = dom.toprettyxml(indent="  ")
            # Remove extra blank lines that minidom might introduce
            pretty_xml = "\n".join([line for line in pretty_xml.split('\n') if line.strip()])
        except Exception as e:
            print(f"Error formatting XML: {e}")
            pretty_xml = xml_str
    
        with open("feed/perplexity.xml", "w") as f:
            f.write(pretty_xml)
        
        print("Generated feed/perplexity.xml")

if __name__ == "__main__":
    scraper = PerplexityScraper()
    scraper.generate_feed()
