import cloudscraper
from bs4 import BeautifulSoup
import rfeed
from datetime import datetime, timedelta, timezone
import re
import xml.dom.minidom

def clean_text(text):
    """
    Removes newlines, tabs, and multiple spaces.
    Returns a single line of text.
    """
    if not text:
        return ""
    # Replace newlines and tabs with a space
    text = re.sub(r'[\n\t\r]+', ' ', text)
    # Replace multiple spaces with a single space
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def replace_cdata(xml_string):
    """
    Post-processing to correctly wrap descriptions in CDATA.
    Unescapes HTML entities inside the description and wraps in CDATA.
    """
    # Pattern to find <description> content
    pattern = r'<description>(.*?)</description>'
    
    def replacer(match):
        content = match.group(1)
        # Unescape common HTML entities that might have been escaped by minidom
        content = content.replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&').replace('&quot;', '"').replace('&apos;', "'")
        return f'<description><![CDATA[{content}]]></description>'
    
    return re.sub(pattern, replacer, xml_string, flags=re.DOTALL)

class ElevenLabsScraper:
    def __init__(self):
        self.url = "https://elevenlabs.io/blog"
        self.scraper = cloudscraper.create_scraper()

    def fetch_articles(self):
        print(f"Fetching {self.url}...")
        try:
            response = self.scraper.get(self.url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            articles = []
            links = soup.find_all('a', href=True)
            
            seen_links = set()
            
            for link in links:
                href = link['href']
                # Exclude categories and pages
                if not href.startswith('/blog/') or href == '/blog' or '/page/' in href or '/category/' in href:
                    continue
                
                full_link = f"https://elevenlabs.io{href}"
                
                if full_link in seen_links:
                    continue
                seen_links.add(full_link)

                # Title extraction: prefer heading tags inside the link
                title = ""
                h_tag = link.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
                if h_tag:
                    title = clean_text(h_tag.get_text(strip=True))
                
                if not title:
                    # Fallback to link text, but be careful of extra text
                    # If the link contains other block elements, get_text might concatenate them
                    # Try to get text of direct children or just the link text
                    title = clean_text(link.get_text(strip=True))
                
                if not title:
                    continue

                articles.append({
                    'title': title,
                    'link': full_link,
                    'pubDate': None, # Will fetch from article page
                    'description': ''
                })
            
            return articles

        except Exception as e:
            print(f"Error fetching articles: {e}")
            return []

    def fetch_article_details(self, url):
        """
        Fetches content and date from the article page.
        Returns (content, pubDate)
        """
        print(f"Fetching details for: {url}")
        try:
            response = self.scraper.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Date Extraction
            pub_date = None
            time_tag = soup.find('time')
            if time_tag and time_tag.has_attr('datetime'):
                try:
                    # ISO format: 2025-11-26T12:43:29.862Z
                    dt_str = time_tag['datetime'].replace('Z', '+00:00')
                    pub_date = datetime.fromisoformat(dt_str)
                except ValueError:
                    pass
            
            if not pub_date:
                 # Fallback to text parsing if datetime attribute fails
                 if time_tag:
                     try:
                         dt = datetime.strptime(time_tag.get_text(strip=True), "%b %d, %Y")
                         pub_date = dt.replace(tzinfo=timezone.utc)
                     except ValueError:
                         pass

            # Content Extraction
            content_div = soup.find('div', class_='rich-text-blog')
            if not content_div:
                content_div = soup.find('article')
            
            content = ""
            if content_div:
                content_parts = []
                for element in content_div.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'ul', 'ol']):
                    if element.name in ['ul', 'ol']:
                        items = [clean_text(li.get_text(strip=True)) for li in element.find_all('li')]
                        if items:
                            content_parts.append(" ".join(items))
                    else:
                        text = clean_text(element.get_text(strip=True))
                        if text:
                            content_parts.append(text)
                content = " ".join(content_parts)
            
            return content, pub_date

        except Exception as e:
            print(f"Error fetching article details: {e}")
            return "", None

    def generate_feed(self):
        articles = self.fetch_articles()
        
        valid_items = []
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=60)
        
        for article in articles:
            content, pub_date = self.fetch_article_details(article['link'])
            
            if pub_date:
                article['pubDate'] = pub_date
            else:
                # If no date found, default to now (or skip? let's default to now to be safe, but maybe log it)
                print(f"Warning: No date found for {article['link']}, using current time.")
                article['pubDate'] = datetime.now(timezone.utc)
            
            if article['pubDate'] >= cutoff_date:
                item = rfeed.Item(
                    title=article['title'],
                    link=article['link'],
                    description=content,
                    pubDate=article['pubDate'],
                    guid=rfeed.Guid(article['link'])
                )
                valid_items.append(item)
            else:
                print(f"Skipping old article: {article['title']} ({article['pubDate']})")
        
        # Sort items by pubDate descending
        valid_items.sort(key=lambda x: x.pubDate, reverse=True)
        
        print(f"Generating feed with {len(valid_items)} items.")
        
        feed = rfeed.Feed(
            title="ElevenLabs Blog",
            link="https://elevenlabs.io/blog",
            description="Latest updates from ElevenLabs",
            language="en-US",
            lastBuildDate=datetime.now(timezone.utc),
            items=valid_items
        )
        
        xml_output = feed.rss()
        
        dom = xml.dom.minidom.parseString(xml_output)
        pretty_xml = dom.toprettyxml(indent="  ")
        
        final_xml = replace_cdata(pretty_xml)
        
        with open("feed/elevenlabs.xml", "w", encoding='utf-8') as f:
            f.write(final_xml)
            
        print("Generated feed/elevenlabs.xml")

if __name__ == "__main__":
    scraper = ElevenLabsScraper()
    scraper.generate_feed()
