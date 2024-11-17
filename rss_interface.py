
from datetime import datetime, timedelta
import json
import os
from feedgenerator import Rss201rev2Feed
import xml.etree.ElementTree as ET

from article import Article

# Load settings from settings.json
with open('rss_settings.json', 'r') as f:
    rss_settings = json.load(f)
with open('settings.json', 'r') as f:
    settings = json.load(f)
    
class RssInterface:
    def __init__(self):
        self.rss_settings = rss_settings
        self.settings = settings
        self.feed = self.create_feed()
        
    def create_feed(self):
        feed_file_path = rss_settings["feed_file_path"]
        
        title = rss_settings["title"]
        link = rss_settings["link"]
        description = rss_settings["description"]
    
        # If the file doesn't exist, create a new feed
        return Rss201rev2Feed(
            title=title,
            link=link,
            description=description
        )
            
    # Function to append a new article to the RSS feed
    def append_articles_to_feed(self, articles):
        for article in articles:
        
            description = f"""
<![CDATA[
<p>{article.score} points by {article.user} on {article.datestring} </p>
<p>{article.generated_article_summary}</p>
<p><a href="{article.comment_link}">Comment Link</a></p>
            """
            
            if hasattr(article, 'comments') and article.comments:
                description += f"<p>Top Comments</p>"
                
                # Add text comments
                description += "<p><ol>"
                for comment in article.comments:
                    description += f"<li>{comment.text}</li>"
                description += "</ol></p>"
                
                # Add html comments
                # description += ""
                # for comment in article.comments:
                #     description += f"<div>{comment.text}</div>"
                #     description += "<br /><hr /><br />"
                    
            description += "]]>"
            
            
            # Convert rank to seconds and subtract from datestring so RSS items show in order
            date_obj = datetime.strptime(article.datestring, "%Y-%m-%dT%H:%M:%S")
            adjusted_date = date_obj - timedelta(seconds=int(settings["max_articles"]) - int(article.rank))
            adjusted_datestring = adjusted_date.strftime("%Y-%m-%dT%H:%M:%S")
            
            date_obj = datetime.now()
            time_increment = timedelta(seconds=int(settings["max_articles"]) - (int(article.rank)*10))
            
            self.feed.add_item(
                title=f"{article.rank}. {article.title}",
                link=article.article_link,
                description=description,
                unique_id=article.comment_link,
                unique_id_is_permalink=True, # not working
                extra_kwargs={
                    "content:encoded": f"<![CDATA[{description}]]>"
                },
                pubdate=date_obj - time_increment
            )
            
    def save_feed(self):
        feed_file_path = rss_settings["feed_file_path"]
        
        # Save the updated feed to file
        with open(feed_file_path, "w", encoding="utf-8") as feed_file:
            self.feed.write(feed_file, 'utf-8')
