
from datetime import datetime, timedelta, timezone
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


class SelfLinkingRssFeed(Rss201rev2Feed):
    """Rss201rev2Feed that emits the atom:self link readers use to confirm feed identity.

    feedgenerator already declares the atom namespace on <rss> but never uses
    it, so the declaration is dead weight without this.
    """

    def __init__(self, *args, feed_url=None, **kwargs):
        self.feed_self_url = feed_url
        super().__init__(*args, **kwargs)

    def rss_attributes(self):
        # Declare the namespace ourselves rather than relying on the installed
        # feedgenerator to do it. Older versions don't, and an undeclared
        # atom: prefix would make the document malformed. Setting the same
        # key the newer versions set keeps this idempotent.
        attrs = super().rss_attributes()
        attrs["xmlns:atom"] = "http://www.w3.org/2005/Atom"
        return attrs

    def add_root_elements(self, handler):
        super().add_root_elements(handler)
        if self.feed_self_url:
            handler.addQuickElement("atom:link", None, {
                "href": self.feed_self_url,
                "rel": "self",
                "type": "application/rss+xml",
            })


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
        return SelfLinkingRssFeed(
            title=title,
            link=link,
            description=description,
            feed_url=rss_settings.get("feed_url")
        )
            
    @staticmethod
    def submission_day(article):
        """The article's true HN submission day, as UTC midnight.

        Falls back to the epoch for an unparseable datestring so a bad record
        sorts to the end of the feed instead of masquerading as brand new.
        """
        try:
            date_obj = datetime.strptime(article.datestring, "%Y-%m-%dT%H:%M:%S")
        except (AttributeError, TypeError, ValueError):
            return datetime.fromtimestamp(0, timezone.utc)
        return date_obj.replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=timezone.utc)

    @classmethod
    def published_date(cls, article):
        """pubDate: the true submission day, with time-of-day derived from rank.

        Readers order by pubDate, so it is the only field that can carry the HN
        ranking. Rank 1 takes the last slot of its day so it sorts first; the
        lowest rank takes midnight. The day is truthful and the exact submission
        time is still shown in the item body.

        Every input is a stored field of the article, so this is identical on
        every rebuild - which is what keeps the feed stable for strict readers.
        """
        slots = max(int(settings["max_articles"]), 1)
        try:
            rank = min(max(int(article.rank), 1), slots)
        except (AttributeError, TypeError, ValueError):
            rank = slots
        return cls.submission_day(article) + timedelta(seconds=round((slots - rank) * 86400 / slots))

    # Function to append a new article to the RSS feed
    def append_articles_to_feed(self, articles):
        # Newest first in document order, then trim to the recent window.
        # article_id breaks ties so the ordering is deterministic.
        ordered = sorted(articles, key=lambda a: (self.published_date(a), str(a.article_id)), reverse=True)
        max_feed_items = int(rss_settings.get("max_feed_items", 150))
        if max_feed_items > 0:
            ordered = ordered[:max_feed_items]

        # A day can carry more than max_articles items (an overlapping re-run
        # repeats a rank), which would collide two items onto one timestamp.
        # Nudge duplicates back a second so every pubDate stays unique and
        # strictly descending; slots are ~29 minutes apart, so this never
        # reorders anything.
        stamped = []
        previous = None
        for article in ordered:
            pubdate = self.published_date(article)
            if previous is not None and pubdate >= previous:
                pubdate = previous - timedelta(seconds=1)
            stamped.append((article, pubdate))
            previous = pubdate

        for article, pubdate in stamped:

            description = f"""
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
            

            self.feed.add_item(
                title=f"{article.rank}. {article.title}",
                link=article.article_link,
                description=description,
                unique_id=article.comment_link,
                unique_id_is_permalink=True, # not working
                extra_kwargs={
                    "content:encoded": description
                },
                pubdate=pubdate
            )
            
    def save_feed(self):
        feed_file_path = rss_settings["feed_file_path"]
        
        # Save the updated feed to file
        with open(feed_file_path, "w", encoding="utf-8") as feed_file:
            self.feed.write(feed_file, 'utf-8')
