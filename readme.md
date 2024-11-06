# HN Summarizer

## Settings overview
### dry_run (bool)
- if `true`: articles will not be added to pickle or RSS.
### load_new_articles (bool)
- if `false`: new articles will not be downloaded or added to the pickle or feed. Use this setting to regenerate the RSS feed without adding new items.
### generate_summaries (bool)
- if `false`: articles will not be submitted to LLM summarizer.
### max_articles (int)
- The number of articles to be downloaded and summarized. Max 30.
### max_items_to_keep (int)
- Maximum number of items that should be kept in the pickle and RSS feed.
### max_comments
- The maximum number of comments to be retrieved.
### override_date (YYYY-MM-DD) (optional)
- `"override_date": "2024-11-01"`

## Tips and Tricks
### Test RSS feed locally by running a local http server with the following command:

`python3 -m http.server`

Then access the feed: http://localhost:8000/feed.xml

If you orphan the http server, find it with the following bash command, then `kill` the process using the ID:

`lsof -i :8000`

