<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
  <xsl:template match="/">
    <html>
      <head>
        <title><xsl:value-of select="rss/channel/title"/></title>
        <style>
          body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; background-color: #f6f8fa; color: #24292e; }
          .header { background: #fff; padding: 20px; border-radius: 6px; box-shadow: 0 1px 3px rgba(0,0,0,0.12); margin-bottom: 20px; }
          h1 { margin: 0; color: #0366d6; font-size: 24px; }
          .description { margin-top: 10px; color: #586069; }
          .item { background: #fff; padding: 20px; border-radius: 6px; box-shadow: 0 1px 3px rgba(0,0,0,0.12); margin-bottom: 15px; }
          .item h3 { margin: 0 0 10px 0; }
          .item h3 a { color: #0366d6; text-decoration: none; }
          .item h3 a:hover { text-decoration: underline; }
          .meta { font-size: 12px; color: #586069; margin-bottom: 15px; }
          .content { line-height: 1.6; font-size: 14px; overflow-wrap: break-word; }
          .content img { max-width: 100%; height: auto; }
        </style>
      </head>
      <body>
        <div class="header">
          <h1><xsl:value-of select="rss/channel/title"/></h1>
          <div class="description"><xsl:value-of select="rss/channel/description"/></div>
          <div class="meta">
            Last Build: <xsl:value-of select="rss/channel/lastBuildDate"/> | 
            <a href="{rss/channel/link}">Website</a>
          </div>
        </div>
        <xsl:for-each select="rss/channel/item">
          <div class="item">
            <h3><a href="{link}"><xsl:value-of select="title"/></a></h3>
            <div class="meta">Published: <xsl:value-of select="pubDate"/></div>
            <div class="content">
              <xsl:value-of select="description" disable-output-escaping="yes"/>
            </div>
          </div>
        </xsl:for-each>
      </body>
    </html>
  </xsl:template>
</xsl:stylesheet>
