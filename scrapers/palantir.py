import requests
from bs4 import BeautifulSoup
import rfeed
from datetime import datetime, timedelta, timezone
import cloudscraper
import json

import requests
from bs4 import BeautifulSoup
import rfeed
from datetime import datetime, timedelta, timezone
import cloudscraper
import json

class PalantirScraper:
    def generate_feed(self):
        scraper = cloudscraper.create_scraper()
        url = "https://www.palantir.com/newsroom/press-releases/"
        
        print(f"Fetching {url}...")
        response = scraper.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        articles = []
        
        data_script = soup.find('script', id='__NEXT_DATA__')
        if not data_script:
            print("Could not find __NEXT_DATA__ script")
            return
    
        try:
            data = json.loads(data_script.string)
            blocks = data['props']['pageProps']['page']['fields']['blocks']
            
            entries = []
            # Navigate through blocks to find customEntries
            for block in blocks:
                if 'fields' in block:
                    # Check for nested blocks
                    if 'blocks' in block['fields']:
                        for subblock in block['fields']['blocks']:
                            if 'customEntries' in subblock.get('fields', {}):
                                entries.extend(subblock['fields']['customEntries'])
                    
                    # Check directly in block (just in case)
                    if 'customEntries' in block['fields']:
                        entries.extend(block['fields']['customEntries'])
            
            print(f"Found {len(entries)} entries.")
            
            for entry in entries:
                try:
                    fields = entry.get('fields', {})
                    headline = fields.get('headline', 'No Title')
                    date_str = fields.get('date')
                    
                    link_obj = fields.get('link', {})
                    link = link_obj.get('fields', {}).get('url') if link_obj else ""
                    
                    if not link:
                        continue
                        
                    # Parse date
                    # Format: 2018-09-04T00:00-07:00
                    pub_date = datetime.now(timezone.utc)
                    if date_str:
                        try:
                            pub_date = datetime.fromisoformat(date_str)
                            # Ensure timezone awareness
                            if pub_date.tzinfo is None:
                                 pub_date = pub_date.replace(tzinfo=timezone.utc)
                        except ValueError:
                            pass
                    
                    description = f"<![CDATA[{headline}]]>"
                    
                    item = rfeed.Item(
                        title=headline,
                        link=link,
                        description=description,
                        pubDate=pub_date,
                        guid=rfeed.Guid(link)
                    )
                    articles.append(item)
                except Exception as e:
                    print(f"Error processing entry: {e}")
                    continue
                    
        except Exception as e:
            print(f"Error parsing JSON data: {e}")
            return
    
        # Sort articles by pubDate descending
        articles.sort(key=lambda x: x.pubDate, reverse=True)
        
        # Filter articles (last 2 months)
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=60)
        original_count = len(articles)
        articles = [a for a in articles if a.pubDate >= cutoff_date]
        print(f"Filtered {original_count - len(articles)} articles older than 60 days. Remaining: {len(articles)}")
    
        feed = rfeed.Feed(
            title="Palantir Press Releases",
            link=url,
            description="Latest press releases from Palantir",
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
    
        with open("feed/palantir.xml", "w") as f:
            f.write(pretty_xml)
        
        print("Generated feed/palantir.xml")

if __name__ == "__main__":
    scraper = PalantirScraper()
    scraper.generate_feed()
