import requests
from bs4 import BeautifulSoup
import rfeed
from datetime import datetime, timedelta, timezone
import cloudscraper
import re

import requests
from bs4 import BeautifulSoup
import rfeed
from datetime import datetime, timedelta, timezone
import cloudscraper
import re

class AmazonScraper:
    def clean_text(self, text):
        if not text:
            return ""
        # Replace newlines and tabs with spaces
        text = text.replace('\n', ' ').replace('\t', ' ').replace('\r', ' ')
        # Collapse multiple spaces
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def fetch_article_content(self, scraper, url):
        try:
            response = scraper.get(url)
            if response.status_code != 200:
                print(f"Failed to fetch article: {response.status_code}")
                return None
                
            soup = BeautifulSoup(response.text, 'html.parser')
            article_body = soup.find('div', class_='ArticlePage-articleBody')
            
            if not article_body:
                return None
                
            # Extract text from content containers
            content_parts = []
            containers = article_body.find_all('div', class_='contentContainer')
            
            for container in containers:
                # Handle text
                text_div = container.find('div', class_='contentItem-role-text')
                if text_div:
                    text = self.clean_text(text_div.get_text(separator=' ', strip=True))
                    if text:
                        content_parts.append(text)
                        continue
                
                # Handle headings
                heading2 = container.find('h2')
                if heading2:
                    text = self.clean_text(heading2.get_text(strip=True))
                    if text:
                        content_parts.append(text)
                        continue
                        
                heading3 = container.find('h3')
                if heading3:
                    text = self.clean_text(heading3.get_text(strip=True))
                    if text:
                        content_parts.append(text)
                        continue

                # Handle lists
                ul = container.find('ul')
                if ul:
                    items = [self.clean_text(li.get_text(strip=True)) for li in ul.find_all('li')]
                    if items:
                        content_parts.append(" ".join(items))
                        continue

            return " ".join(content_parts)
            
        except Exception as e:
            print(f"Error fetching article content: {e}")
            return None

    def generate_feed(self):
        scraper = cloudscraper.create_scraper()
        url = "https://www.aboutamazon.com/artificial-intelligence-ai-news"
        
        print(f"Fetching {url}...")
        response = scraper.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        articles = []
        
        # Only select cards that are actual articles (promo-card-v2--articlerouting)
        # and exclude "You might also like" cards (promo-card-v2--listlandscape)
        cards = soup.find_all('div', class_='promo-card-v2--articlerouting')
        print(f"Found {len(cards)} articles.")
        
        for card in cards:
            try:
                # Title and Link
                title_div = card.find('div', class_='promo-card-v2__title')
                if not title_div:
                    continue
                    
                title_link = title_div.find('a')
                if not title_link:
                    continue
                    
                title = title_link.get_text(strip=True)
                link = title_link['href']
                
                # Description
                desc_div = card.find('div', class_='promo-card-v2__excerpt')
                description_text = desc_div.get_text(strip=True) if desc_div else title
                description = description_text
                
                # Date
                date_div = card.find('div', class_='card-meta__published')
                date_str = date_div.get_text(strip=True) if date_div else ""
                
                # Parse date: "Dec. 4, 2025"
                pub_date = datetime.now(timezone.utc)
                if date_str:
                    try:
                        clean_date_str = date_str.replace(".", "")
                        pub_date = datetime.strptime(clean_date_str, "%b %d, %Y")
                        pub_date = pub_date.replace(tzinfo=timezone.utc)
                    except ValueError as e:
                        print(f"Error parsing date '{date_str}': {e}")
                        pass
                
                # Fetch full content
                print(f"Fetching content for: {title}")
                full_content = self.fetch_article_content(scraper, link)
                if full_content:
                    description = full_content
                else:
                    # Fallback to excerpt
                    desc_div = card.find('div', class_='promo-card-v2__excerpt')
                    description_text = desc_div.get_text(strip=True) if desc_div else title
                    description = description_text
    
                item = rfeed.Item(
                    title=title,
                    link=link,
                    description=description,
                    pubDate=pub_date,
                    guid=rfeed.Guid(link)
                )
                articles.append(item)
                
            except Exception as e:
                print(f"Error processing card: {e}")
                continue
    
        # Sort articles by pubDate descending
        articles.sort(key=lambda x: x.pubDate, reverse=True)
        
        # Filter articles (last 2 months)
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=60)
        original_count = len(articles)
        articles = [a for a in articles if a.pubDate >= cutoff_date]
        print(f"Filtered {original_count - len(articles)} articles older than 60 days. Remaining: {len(articles)}")
    
        feed = rfeed.Feed(
            title="Amazon AI News",
            link=url,
            description="Latest news about AI at Amazon",
            language="en-US",
            lastBuildDate=datetime.now(timezone.utc),
            items=articles
        )
    
        xml_str = feed.rss()
        
        # Format XML
        try:
            from xml.dom import minidom
            dom = minidom.parseString(xml_str)
            pretty_xml = dom.toprettyxml(indent="  ")
            # Inject stylesheet
            pretty_xml = pretty_xml.replace('<?xml version="1.0" ?>', '<?xml version="1.0" ?>\n<?xml-stylesheet type="text/xsl" href="style.xsl"?>')
            
            # Remove extra blank lines that minidom might introduce
            pretty_xml = "\n".join([line for line in pretty_xml.split('\n') if line.strip()])
            
            # Post-process to add CDATA
            def replace_cdata(match):
                content = match.group(1)
                # Unescape basic XML entities
                content = content.replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&').replace('&quot;', '"').replace('&apos;', "'")
                return f"<description><![CDATA[{content}]]></description>"
                
            pretty_xml = re.sub(r'<description>(.*?)</description>', replace_cdata, pretty_xml, flags=re.DOTALL)
        except Exception as e:
            print(f"Error formatting XML: {e}")
            pretty_xml = xml_str
    
        with open("feed/amazon.xml", "w") as f:
            f.write(pretty_xml)
        
        print("Generated feed/amazon.xml")

if __name__ == "__main__":
    scraper = AmazonScraper()
    scraper.generate_feed()
