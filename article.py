import requests
from bs4 import BeautifulSoup
import lxml.html.clean
import json
import time
import importlib

import hn_api
# from llm_interface import summarize
from summarizer import summarize

# Load settings from settings.json
with open("settings.json", "r") as f:
    settings = json.load(f)

RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}
MAX_RETRIES = 5
RETRY_BACKOFF_BASE = 2  # seconds; delay = base ** attempt
REQUEST_USER_AGENT = settings.get("request_user_agent", "hn_summaries/1.0")
REQUEST_TIMEOUT_SECONDS = settings.get("request_timeout_seconds", 45)
CACHE_TTL_SECONDS = settings.get("request_cache_ttl_seconds", 3600)

_SOUP_CACHE = {}


def _retry_delay_seconds(response, attempt):
    if response is not None:
        retry_after = response.headers.get("Retry-After")
        if retry_after:
            try:
                return max(0, int(retry_after))
            except ValueError:
                pass
    return RETRY_BACKOFF_BASE ** attempt

class Article:
    def __init__(self, rank, title, article_link, score, user, article_id, datestring, generate_summaries, kids=None):
        self.rank = rank
        self.title = title
        self.article_link = article_link
        self.score = score
        self.user = user
        self.article_id = article_id
        self.datestring = datestring
        self.generate_summaries = generate_summaries
        self.kids = kids or []
        self.error_raise = False
        self.error_msg = None
        self.comment_link = settings["comment_url"] + str(self.article_id)
        self.generated_article_summary = None
        self.top_text = None
        self.comments = []
        self.has_comments = False
        
        if self.generate_summaries:
            # self.retrieve_llm_article_summary()
            self.retrieve_openai_article_summary()
            self.retrieve_comments()
        
        if hasattr(self, 'comments') and self.comments:
            self.has_comments = True
            

    class Comment:
        def __init__(self, position, text):
            self.position = position
            self.text = text

        def __repr__(self):
            return f"Comment(position={self.position}, text={self.text})"

    def __repr__(self):
        output = f"""
Article(
    rank={self.rank}, 
    title={self.title}, 
    article_link={self.article_link}, 
    comment_link={self.comment_link}, 
    score={self.score}, 
    user={self.user}, 
    article_id={self.article_id}, 
    datestring={self.datestring}, 
    generated_article_summary={self.generated_article_summary},
"""
        if self.top_text:
            output += f"    top_text:{self.top_text}\n"

        if self.has_comments:
            output += f"    Comments: {self.comments},\n"
            
        output += f"    error_raised={self.error_raise})\n"
        output += f"    error_msg={self.error_msg})"
        return output
    
    def retrieve_llm_article_summary(self):
        generated_article_summary = ""

        try:
            Document = importlib.import_module("readability").Document
        except ImportError:
            self.error_raise = True
            self.error_msg = "readability package is not installed"
            return
        
        # Fetch the article content
        article_soup = self.fetch_soup(self.article_link)
        
        # Extract the page contents, clean out the non-content, and extract the text
        if article_soup:
            # doc = Document(article_soup)
            cleaner = lxml.html.clean.Cleaner(style=False, scripts=False, javascript=False, comments=False, page_structure=False, safe_attrs_only=False)       
            cleaned_html = cleaner.clean_html(article_soup.get_text()) # TODO: improve code to pull article text
            doc = Document(cleaned_html)
            content = BeautifulSoup(doc.summary(), 'html.parser').get_text()
            
            # summarize the content
            summary = ""
            try:
                summary = summarize(content)
            except Exception as e:
                self.error_raise = True
                self.error_msg = str(e)
            
            self.generated_article_summary = summary
            
    def retrieve_openai_article_summary(self):
        # Fetch the article content to confirm it is reachable before summarizing
        article_soup = self.fetch_soup(self.article_link)

        if article_soup:
            summary = ""
            try:
                summary = summarize(self.article_link)
            except ValueError as e:
                self.error_raise = True
                self.error_msg = str(e)

            self.generated_article_summary = summary

    def retrieve_comments(self):
        # Fetch top-level comments via the HN API using the story's kids list
        comment_position = 1
        for kid_id in self.kids:
            item = hn_api.get_item(kid_id)

            # Skip deleted, dead, or empty comments
            if not item or item.get("deleted") or item.get("dead") or not item.get("text"):
                continue

            # The API returns comment text as HTML; strip tags to plain text
            comment_text = BeautifulSoup(item["text"], "html.parser").get_text()

            self.comments.append(Article.Comment(comment_position, comment_text))

            if comment_position >= settings["max_comments"]:
                break

            comment_position += 1

    def fetch_soup(self, url):
        cache_entry = _SOUP_CACHE.get(url)
        now = time.time()
        if cache_entry and now - cache_entry["timestamp"] <= CACHE_TTL_SECONDS:
            return cache_entry["soup"]

        for attempt in range(MAX_RETRIES):
            try:
                response = requests.get(url, timeout=REQUEST_TIMEOUT_SECONDS, headers={"User-Agent": REQUEST_USER_AGENT})
                response.raise_for_status()
                soup = BeautifulSoup(response.content, 'html.parser')
                _SOUP_CACHE[url] = {
                    "timestamp": time.time(),
                    "soup": soup,
                }
                return soup
            except requests.exceptions.HTTPError as e:
                status = e.response.status_code if e.response is not None else None
                if status in RETRYABLE_STATUS_CODES and attempt < MAX_RETRIES - 1:
                    delay = _retry_delay_seconds(e.response, attempt)
                    print(f"HTTP {status} from {url}, retrying in {delay}s (attempt {attempt + 1}/{MAX_RETRIES})")
                    time.sleep(delay)
                else:
                    self.error_raise = True
                    self.error_msg = str(e)
                    return None
            except requests.exceptions.RequestException as e:
                if attempt < MAX_RETRIES - 1:
                    delay = RETRY_BACKOFF_BASE ** attempt
                    print(f"Request error for {url}: {e}, retrying in {delay}s (attempt {attempt + 1}/{MAX_RETRIES})")
                    time.sleep(delay)
                else:
                    self.error_raise = True
                    self.error_msg = str(e)
                    return None