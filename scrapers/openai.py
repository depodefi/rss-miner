import cloudscraper
from bs4 import BeautifulSoup
import rfeed
from datetime import datetime, timezone
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

class OpenAIScraper:
    def __init__(self):
        self.rss_url = "https://openai.com/news/rss.xml"
        self.scraper = cloudscraper.create_scraper()

    def fetch_article_content(self, url):
        """
        Fetches the full content of the article to provide a longer description.
        """
        print(f"Fetching details for: {url}")
        try:
            response = self.scraper.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # OpenAI articles structure varies, but usually content is in main
            # or in a specific block.
            content = ""
            
            # Try to find the main content container
            # 1. 'ui-block--text' is common in their new design
            content_divs = soup.find_all(class_=lambda x: x and 'ui-block' in x)
            
            paragraphs = []
            
            if content_divs:
                for div in content_divs:
                    for p in div.find_all('p'):
                         text = clean_text(p.get_text(strip=True))
                         if text:
                             paragraphs.append(text)
            else:
                 # Fallback: find all paragraphs in main or article
                 container = soup.find('article') or soup.find('main') or soup.body
                 if container:
                     for p in container.find_all('p'):
                         # Filter out short/navigational text
                         text = clean_text(p.get_text(strip=True))
                         if len(text) > 50: # arbitrary filter for "content-like" paragraphs
                             paragraphs.append(text)

            if paragraphs:
                # Join with explicit line breaks for readability in feed readers that support it, 
                # or just space. HTML description is usually best.
                # Let's use HTML paragraphs.
                content = "".join([f"<p>{p}</p>" for p in paragraphs])
            
            return content

        except Exception as e:
            print(f"Error fetching article details for {url}: {e}")
            return None

    def generate_feed(self):
        print(f"Fetching RSS feed from {self.rss_url}...")
        try:
            response = self.scraper.get(self.rss_url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'xml')
            
            items = soup.find_all('item')
            # Limit to recent items to avoid long running times
            items = items[:30]
            feed_items = []
            
            print(f"Found {len(soup.find_all('item'))} items in RSS feed. Processing recent {len(items)}...")
            
            for item in items:
                title = item.find('title').get_text(strip=True)
                link = item.find('link').get_text(strip=True)
                pub_date_str = item.find('pubDate').get_text(strip=True)
                
                # Parse date
                try:
                    pub_date = datetime.strptime(pub_date_str, "%a, %d %b %Y %H:%M:%S %Z").replace(tzinfo=timezone.utc)
                except ValueError:
                    # Try varying formats if needed, but RSS usually standard
                    try: 
                        pub_date = datetime.strptime(pub_date_str, "%a, %d %b %Y %H:%M:%S %z")
                    except ValueError:
                         pub_date = datetime.now(timezone.utc)
                
                # Original description
                description = item.find('description').get_text(strip=True) if item.find('description') else ""
                
                # Enrich content
                full_content = self.fetch_article_content(link)
                
                if full_content:
                    description = full_content
                else:
                    print(f"Using original description for {link}")

                feed_item = rfeed.Item(
                    title=title,
                    link=link,
                    description=description,
                    pubDate=pub_date,
                    guid=rfeed.Guid(link)
                )
                feed_items.append(feed_item)
            
            # Create Feed
            feed = rfeed.Feed(
                title="OpenAI News (Enriched)",
                link="https://openai.com/news/",
                description="Latest news from OpenAI with full article content.",
                language="en-US",
                lastBuildDate=datetime.now(timezone.utc),
                items=feed_items
            )
            
            xml_output = feed.rss()
            
            dom = xml.dom.minidom.parseString(xml_output)
            pretty_xml = dom.toprettyxml(indent="  ")
            
            # Inject stylesheet
            pretty_xml = pretty_xml.replace('<?xml version="1.0" ?>', '<?xml version="1.0" ?>\n<?xml-stylesheet type="text/xsl" href="style.xsl"?>')
            
            final_xml = replace_cdata(pretty_xml)
            
            with open("feed/openai.xml", "w", encoding='utf-8') as f:
                f.write(final_xml)
                
            print("Generated feed/openai.xml")

        except Exception as e:
            print(f"Error generating feed: {e}")

if __name__ == "__main__":
    scraper = OpenAIScraper()
    scraper.generate_feed()
