import requests
from bs4 import BeautifulSoup
from readability import Document
import lxml.html.clean
import json

from llm_interface import summarize

# Load settings from settings.json
with open("settings.json", "r") as f:
    settings = json.load(f)

class Article:
    def __init__(self, rank, title, article_link, score, user, article_id, datestring, generate_summaries):
        self.rank = rank
        self.title = title
        self.article_link = article_link
        self.score = score
        self.user = user
        self.article_id = article_id
        self.datestring = datestring
        self.generate_summaries = generate_summaries
        self.error_raise = False
        self.error_msg = None
        self.comment_link = settings["comment_url"] + self.article_id
        self.generated_article_summary = self.retrieve_article_summary() if self.generate_summaries else ""  # Generate the article summary if required
        self.generated_comment_summary = self.retrieve_comment_summary() if self.generate_summaries else ""  # Generate the comment summary

    def __repr__(self):
        return f"Article(rank={self.rank}, title={self.title}, article_link={self.article_link}, comment_link={self.comment_link}, score={self.score}, user={self.user}, article_id={self.article_id}, datestring={self.datestring}, generated_article_summary={self.generated_article_summary}, generated_comment_summary={self.generated_comment_summary})"
    
    def retrieve_article_summary(self):
        generated_article_summary = ""
        
        # TODO: if Show|Ask|Launch HN....
        
        # Fetch the article content
        article_soup = self.fetch_soup(self.article_link)
        
        # Extract the page contents, clean out the non-content, and extract the text
        if article_soup:
            # doc = Document(article_soup)
            cleaner = lxml.html.clean.Cleaner(style=False, scripts=False, javascript=False, comments=False, page_structure=False, safe_attrs_only=False)       
            cleaned_html = cleaner.clean_html(article_soup.get_text())
            doc = Document(cleaned_html)
            content = BeautifulSoup(doc.summary(), 'html.parser').get_text()
            
            # summarize the content
            generated_article_summary = summarize(content)
            
        return generated_article_summary
    
    def retrieve_comment_summary(self):
        generated_comment_summary = ""
        
        # Fetch the comments page
        comments_soup = self.fetch_soup(self.comment_link)
        
        if comments_soup:
        #     # Find all <span> elements with class "commtext"
        #     commtext_spans = comments_soup.find_all("span", attrs={"class": "commtext"}).get_text()
            
            # doc = Document(comments_soup)
            cleaner = lxml.html.clean.Cleaner(style=False, scripts=False, javascript=False, comments=False, page_structure=False, safe_attrs_only=False)       
            cleaned_html = cleaner.clean_html(comments_soup.get_text())
            doc = Document(cleaned_html)
            content = BeautifulSoup(doc.summary(), 'html.parser').get_text()
            
            generated_comment_summary = summarize(content)
            
        return generated_comment_summary
    
    def fetch_soup(self, url):
        soup = None
        
        # Fetch the HTML content
        try:
            response = requests.get(url)
            response.raise_for_status()  # Raise an error for bad status codes
            # Parse the HTML content
            soup = BeautifulSoup(response.content, 'html.parser')
        except requests.exceptions.RequestException as e:
            self.error_raised = True
            self.error_msg = str(e)
            
        return soup