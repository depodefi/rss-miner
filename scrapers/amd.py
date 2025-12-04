import requests
from bs4 import BeautifulSoup
from rfeed import *
import datetime
import xml.dom.minidom
import os
import re
from dateutil import parser as date_parser

def extract_text(soup_element):
    # Remove unwanted tags
    for tag in soup_element.find_all(['script', 'style', 'h1', 'div', 'pre']):
        # We remove divs because the main content is directly in article as p/ul tags
        # But wait, related-documents-line is a div.
        # If there are other divs with content, we might lose them.
        # Let's be more specific with removals first.
        pass

    # Specific removals
    for tag in soup_element.find_all('h1', class_='article-heading'):
        tag.decompose()
    
    for tag in soup_element.find_all('div', class_='related-documents-line'):
        tag.decompose()
        
    for tag in soup_element.find_all('p', class_='spr-ir-news-article-date'):
        tag.decompose()

    # Remove contact info if in pre
    for tag in soup_element.find_all('pre'):
        tag.decompose()

    # Remove scripts and styles
    for tag in soup_element.find_all(['script', 'style']):
        tag.decompose()

    # Get text with separators
    text = soup_element.get_text(separator=' ', strip=True)
    # Collapse multiple spaces
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def generate():
    rss_url = "https://ir.amd.com/news-events/press-releases/rss"
    try:
        response = requests.get(rss_url, headers={'User-Agent': 'Mozilla/5.0'})
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Error fetching RSS URL: {e}")
        return

    # Parse RSS XML
    soup = BeautifulSoup(response.content, 'xml')
    items = soup.find_all('item')
    
    feed_items = []
    
    print(f"Found {len(items)} items in RSS feed. Processing...")
    
    for item in items:
        title = item.find('title').get_text(strip=True)
        link = item.find('link').get_text(strip=True)
        pub_date_str = item.find('pubDate').get_text(strip=True)
        
        # Parse date
        try:
            pub_date = date_parser.parse(pub_date_str)
        except Exception as e:
            print(f"Error parsing date {pub_date_str}: {e}")
            pub_date = datetime.datetime.now()

        description = ""
        
        # Fetch full article content
        try:
            # print(f"Fetching article: {link}")
            art_response = requests.get(link, headers={'User-Agent': 'Mozilla/5.0'})
            art_response.raise_for_status()
            art_soup = BeautifulSoup(art_response.content, 'html.parser')
            
            # Selector: article.full-news-article
            content_div = art_soup.find('article', class_='full-news-article')
            
            if content_div:
                description = extract_text(content_div)
            else:
                print(f"Could not find content div for {link}")
                # Fallback to RSS description
                rss_desc = item.find('description')
                if rss_desc:
                    description = rss_desc.get_text(strip=True)

        except Exception as e:
            print(f"Failed to fetch/parse article {link}: {e}")
            # Fallback to RSS description
            rss_desc = item.find('description')
            if rss_desc:
                description = rss_desc.get_text(strip=True)

        feed_item = Item(
            title=title,
            link=link,
            description=description,
            author="AMD",
            guid=Guid(link),
            pubDate=pub_date
        )
        feed_items.append(feed_item)

    # Sort items by pubDate descending
    feed_items.sort(key=lambda x: x.pubDate, reverse=True)
    
    feed = Feed(
        title="AMD Press Releases",
        link="https://ir.amd.com/news-events/press-releases",
        description="Latest press releases from AMD",
        language="en-US",
        lastBuildDate=datetime.datetime.now(),
        items=feed_items
    )
    
    rss_content = feed.rss()
    dom = xml.dom.minidom.parseString(rss_content)
    pretty_xml = dom.toprettyxml(indent="  ")
    
    # Post-process to add CDATA
    def replace_cdata(match):
        content = match.group(1)
        # Unescape basic XML entities
        content = content.replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&').replace('&quot;', '"').replace('&apos;', "'")
        return f"<description><![CDATA[{content}]]></description>"
        
    pretty_xml = re.sub(r'<description>(.*?)</description>', replace_cdata, pretty_xml, flags=re.DOTALL)
    
    os.makedirs("feed", exist_ok=True)
    
    with open("feed/amd.xml", "w") as f:
        f.write(pretty_xml)
    print(f"Generated feed/amd.xml with {len(feed_items)} items.")

if __name__ == "__main__":
    generate()
