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
        self.generated_article_summary = None 
        self.comments = []
        self.has_comments = False
        
        if self.generate_summaries:
            self.retrieve_article_summary()
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
        if self.has_comments:
            output += f"    Comments: {self.comments},\n"
            
        output += f"    error_raised={self.error_raise})\n"
        output += f"    error_msg={self.error_msg})"
        return output
    
    def retrieve_article_summary(self):
        generated_article_summary = ""
        
        # TODO: if Show|Ask|Launch HN....
        
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
            except ValueError as e:
                self.error_raise = True
                self.error_msg = str(e)
            
            self.generated_article_summary = summary
    
    def retrieve_comments(self):
        # Fetch the comments page
        comments_soup = self.fetch_soup(self.comment_link)
        
        comment_position = 1
        comment_items = comments_soup.find_all("td", attrs={"indent": "0"})
        for table in comment_items:            
            tr = table.parent
            
            comment_text = tr.find("div", attrs={"class": "commtext c00"}).get_text() # Get the comment text
            # comment_text = tr.find("div", attrs={"class": "commtext c00"}).decode_contents() # Get the HTML content instead of just the text
            self.comments.append(Article.Comment(comment_position, comment_text))
            
            if comment_position >= settings["max_comments"]:
                break
            
            comment_position += 1
            
    def fetch_soup(self, url):
        soup = None
        
        # Fetch the HTML content
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()  # Raise an error for bad status codes
            # Parse the HTML content
            soup = BeautifulSoup(response.content, 'html.parser')
        except requests.exceptions.RequestException as e:
            self.error_raised = True
            self.error_msg = str(e)
            
        return soup