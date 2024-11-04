
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
        
        # Check if the feed file exists
        if os.path.exists(feed_file_path):
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
<h2>Article Summary</h2>
<p>{article.generated_article_summary}</p>
<h2>Comment Summary</h2>
<a href="{article.comment_link}">Comment Link</a>
<p>{article.generated_comment_summary}</p>
]]
            """
            
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
            
            
    # def parse_pretty_txt():
    #     articles = []
    #     rank = 1
    #     with open(settings["logging_folder"] + "pretty.txt", "r") as file:
    #         lines = file.readlines()
    #         for i in range(0, len(lines), 10):  # Each article block is 8 lines long
    #             title = lines[i].split(": ")[1].strip()
    #             article_link = lines[i+1].split(": ")[1].strip()
    #             comment_link = lines[i+2].split(": ")[1].strip()
    #             score = lines[i+3].split(": ")[1].strip().split()[0]
    #             user = lines[i+4].split(": ")[1].strip()
    #             date = lines[i+5].split(": ")[1].strip()
    #             article = Article(rank=rank, title=title, article_link=article_link, score=score, user=user, article_id="0", datestring=date, generate_summaries=False)
    #             article.comment_link = comment_link
    #             article.generated_article_summary = lines[i+6].split(": ")[1].strip()
    #             article.generated_comment_summary = lines[i+7].split(": ")[1].strip()
            
    #             articles.append(article)
    #             rank += 1
    #     return articles


# articles = parse_pretty_txt()
# print(len(articles))


# Path to your feed file
# feed_file_path = rss_settings["feed_file_path"]

# Create or load the feed
# feed = create_or_load_feed()

