# Feedly Client

This is basic Feedly Client designed to get YouTube videos from unread articles. It also can save the videos to a playlist on YouTube, and mark the source articles as read on Feedly. 

## Using

* `pylint` as a linter
* `httpx` for requests
* `BeautifulSoup` for HTML parsing

## Examples

Getting a list of unread articles from Feedly
```python
from feedly import FeedlyApiClient
import json
import os

# Configuration input
client_id = '[FEEDLY_CLIENT_ID]'
api_key = '[FEEDLY_API_KEY]'
secrets_file_loc = '[GOOGLE_SECRETS_FILE_LOCATION]'

# Client initialization
client = FeedlyApiClient(client_id, api_key, secrets_file_loc)

# Get videos & articles
youtube_links, read_article_ids = client.get_all_youtube_links()

# Add videos to Scraper playlist
for video in youtube_links:
   TODO fix needing to auth on each video save
   response = client.add_video_to_playlist(video.split('=')[1])

# Mark article as read
response = client.mark_articles_as_read(read_article_ids)
```

## External Docs
* [Feedly API Documentation](https://developers.feedly.com/)
* [BeautifulSoup Documentation](https://www.crummy.com/software/BeautifulSoup/bs4/doc/index.html)

