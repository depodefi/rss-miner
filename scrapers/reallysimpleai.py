import requests
from bs4 import BeautifulSoup
from rfeed import *
import datetime
import xml.dom.minidom
import os
import re
from dateutil import parser as date_parser

class ReallySimpleAIScraper:
    def generate_feed(self):
        rss_url = "https://reallysimpleai.blogspot.com/feeds/posts/default?alt=rss"
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
            title_tag = item.find('title')
            title = title_tag.get_text(strip=True) if title_tag else "No Title"

            link_tag = item.find('link')
            link = link_tag.get_text(strip=True) if link_tag else ""

            pub_date_str = item.find('pubDate').get_text(strip=True) if item.find('pubDate') else ""

            # Parse date
            if pub_date_str:
                try:
                    pub_date = date_parser.parse(pub_date_str)
                except Exception as e:
                    print(f"Error parsing date {pub_date_str}: {e}")
                    pub_date = datetime.datetime.now()
            else:
                pub_date = datetime.datetime.now()

            description = ""
            rss_desc = item.find('description')
            if rss_desc:
                description = rss_desc.get_text(strip=True)

            feed_item = Item(
                title=title,
                link=link,
                description=description,
                author="Really Simple AI",
                guid=Guid(link),
                pubDate=pub_date
            )
            feed_items.append(feed_item)

        # Sort items by pubDate descending
        feed_items.sort(key=lambda x: x.pubDate, reverse=True)

        feed = Feed(
            title="Really Simple AI",
            link="https://reallysimpleai.blogspot.com/",
            description="Latest news from Really Simple AI",
            language="en-US",
            lastBuildDate=datetime.datetime.now(),
            items=feed_items
        )

        rss_content = feed.rss()
        dom = xml.dom.minidom.parseString(rss_content)
        pretty_xml = dom.toprettyxml(indent="  ")

        # Inject stylesheet
        pretty_xml = pretty_xml.replace('<?xml version="1.0" ?>', '<?xml version="1.0" ?>\n<?xml-stylesheet type="text/xsl" href="style.xsl"?>')

        # Post-process to add CDATA
        def replace_cdata(match):
            content = match.group(1)
            # Unescape basic XML entities to avoid double escaping when wrapping in CDATA
            content = content.replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&').replace('&quot;', '"').replace('&apos;', "'")
            return f"<description><![CDATA[{content}]]></description>"

        pretty_xml = re.sub(r'<description>(.*?)</description>', replace_cdata, pretty_xml, flags=re.DOTALL)

        os.makedirs("feed", exist_ok=True)

        with open("feed/reallysimpleai.xml", "w") as f:
            f.write(pretty_xml)
        print(f"Generated feed/reallysimpleai.xml with {len(feed_items)} items.")

if __name__ == "__main__":
    scraper = ReallySimpleAIScraper()
    scraper.generate_feed()
