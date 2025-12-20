import requests
from bs4 import BeautifulSoup
from rfeed import *
import datetime
import xml.dom.minidom
import os
import re

def extract_text(soup_element):
    # Remove unwanted tags
    for tag in soup_element.find_all(['script', 'style']):
        tag.decompose()
            
    # Get text with separators
    text = soup_element.get_text(separator=' ', strip=True)
    # Collapse multiple spaces
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

class NvidiaScraper:
    def generate_feed(self):
        url = "https://blogs.nvidia.com/blog/category/generative-ai/"
        try:
            response = requests.get(url)
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"Error fetching URL: {e}")
            return

        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find all articles
        articles = soup.find_all('article')
        
        items = []
        seen_links = set()
        
        print(f"Found {len(articles)} articles. Processing...")
        
        for article in articles:
            # Link
            link_tag = article.find('a', class_='aggregation-card-link')
            if not link_tag:
                # Try title link
                title_header = article.find(['h2', 'h3'], class_='entry-title')
                if title_header:
                    link_tag = title_header.find('a')
            
            if not link_tag:
                continue
                
            link = link_tag.get('href')
            if link in seen_links:
                continue
            seen_links.add(link)
            
            # Title
            title = ""
            title_header = article.find(['h2', 'h3', 'p'], class_='entry-title')
            if title_header:
                title = title_header.get_text(strip=True)
            
            if not title:
                title = "No Title"
                
            # Description
            description = ""
            excerpt_div = article.find(['div'], class_=['entry-excerpt', 'article-excerpt'])
            if excerpt_div:
                p_tag = excerpt_div.find('p')
                if p_tag:
                    description = p_tag.get_text(strip=True)
            
            # Fetch article page for date and description
            pub_date = datetime.datetime.now()
            try:
                # print(f"Fetching article: {link}")
                art_response = requests.get(link)
                art_response.raise_for_status()
                art_soup = BeautifulSoup(art_response.content, 'html.parser')
                
                # <meta property="article:published_time" content="2025-12-02T16:00:27+00:00" />
                meta_date = art_soup.find('meta', property='article:published_time')
                if meta_date:
                    date_str = meta_date.get('content')
                    # Parse ISO format
                    # 2025-12-02T16:00:27+00:00
                    try:
                        pub_date = datetime.datetime.fromisoformat(date_str)
                    except ValueError:
                        # Handle potential parsing errors or different formats
                        pass
                
                # Get full content
                content_div = art_soup.find('div', class_='entry-content')
                if content_div:
                    # Remove reading time if present
                    reading_time = content_div.find('span', class_='bsf-rt-reading-time')
                    if reading_time:
                        reading_time.decompose()
                    
                    # Remove social placeholder if present
                    social_placeholder = content_div.find('div', class_='has-social-placeholder')
                    if social_placeholder:
                        social_placeholder.decompose()

                    description = extract_text(content_div)
                
                # Fallback to meta description if content extraction failed
                if not description:
                    meta_desc = art_soup.find('meta', attrs={'name': 'description'})
                    if not meta_desc:
                        meta_desc = art_soup.find('meta', property='og:description')
                    
                    if meta_desc:
                        description = meta_desc.get('content')
                        
            except Exception as e:
                print(f"Failed to fetch/parse article {link}: {e}")
                
            item = Item(
                title=title,
                link=link,
                description=description,
                author="NVIDIA",
                guid=Guid(link),
                pubDate=pub_date
            )
            items.append(item)

        # Sort items by pubDate descending (newest first)
        items.sort(key=lambda x: x.pubDate, reverse=True)
        
        feed = Feed(
            title="NVIDIA Generative AI News",
            link="https://blogs.nvidia.com/blog/category/generative-ai/",
            description="Latest news from NVIDIA Generative AI Blog",
            language="en-US",
            lastBuildDate=datetime.datetime.now(),
            items=items
        )
        
        rss_content = feed.rss()
        dom = xml.dom.minidom.parseString(rss_content)
        pretty_xml = dom.toprettyxml(indent="  ")
        # Inject stylesheet
        pretty_xml = pretty_xml.replace('<?xml version="1.0" ?>', '<?xml version="1.0" ?>\n<?xml-stylesheet type="text/xsl" href="style.xsl"?>')
        
        
        # Post-process to add CDATA
        def replace_cdata(match):
            content = match.group(1)
            # Unescape basic XML entities
            content = content.replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&').replace('&quot;', '"').replace('&apos;', "'")
            return f"<description><![CDATA[{content}]]></description>"
            
        pretty_xml = re.sub(r'<description>(.*?)</description>', replace_cdata, pretty_xml, flags=re.DOTALL)
        
        os.makedirs("feed", exist_ok=True)
        
        with open("feed/nvidia.xml", "w") as f:
            f.write(pretty_xml)
        print(f"Generated feed/nvidia.xml with {len(items)} items.")

if __name__ == "__main__":
    scraper = NvidiaScraper()
    scraper.generate_feed()
