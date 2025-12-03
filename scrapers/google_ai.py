import requests
from bs4 import BeautifulSoup
from rfeed import *
import datetime
import xml.dom.minidom
import os
import re
from dateutil import parser as date_parser

def extract_text(soup_element):
    # Remove specific Google blog elements
    for tag in soup_element.find_all(['uni-article-speakable', 'uni-reading-time', 'script', 'style']):
        tag.decompose()
        
    for div in soup_element.find_all('div', class_=['uni-social-share', 'article-share__wrapper', 'article-meta__container']):
        div.decompose()

    # Get text with separators
    text = soup_element.get_text(separator=' ', strip=True)
    # Collapse multiple spaces
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def generate():
    rss_url = "https://blog.google/technology/ai/rss/"
    try:
        response = requests.get(rss_url)
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
            art_response = requests.get(link)
            art_response.raise_for_status()
            art_soup = BeautifulSoup(art_response.content, 'html.parser')
            
            # Find content div
            # Selector: div.uni-blog-article-container or div.article-container__content
            content_div = art_soup.find('div', class_='uni-blog-article-container')
            if not content_div:
                content_div = art_soup.find('div', attrs={'slot': 'uni-short-post-description-slot'})
            if not content_div:
                content_div = art_soup.find('div', class_='collection-detail__description')
            if not content_div:
                content_div = art_soup.find('div', class_='article-container__content')
            
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
            author="Google AI",
            guid=Guid(link),
            pubDate=pub_date
        )
        feed_items.append(feed_item)

    # Sort items by pubDate descending
    feed_items.sort(key=lambda x: x.pubDate, reverse=True)
    
    feed = Feed(
        title="Google AI Blog",
        link="https://blog.google/technology/ai/",
        description="Latest news from Google AI",
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
        # Unescape basic XML entities to avoid double escaping when wrapping in CDATA
        # But wait, rfeed might have already escaped them.
        # If rfeed escaped '<' as '&lt;', we want to revert it to '<' inside CDATA.
        content = content.replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&').replace('&quot;', '"').replace('&apos;', "'")
        return f"<description><![CDATA[{content}]]></description>"
        
    pretty_xml = re.sub(r'<description>(.*?)</description>', replace_cdata, pretty_xml, flags=re.DOTALL)
    
    os.makedirs("feed", exist_ok=True)
    
    with open("feed/google.xml", "w") as f:
        f.write(pretty_xml)
    print(f"Generated feed/google.xml with {len(feed_items)} items.")

if __name__ == "__main__":
    generate()
