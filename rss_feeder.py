from bs4 import BeautifulSoup
from collections import defaultdict
import httpx
import json
import re
import feedparser


from parsers import NYTParser
from feedly import FeedlyApiClient


CLIENT_ID = 'ede62ec0-5773-49b1-bfe7-c2843e0f4dec'
ACCESS_TOKEN = 'Azps7uUKhDZwbAVqhVZI27kviVz0bb7709m0GJF6OsA0DWppd-zzgCnUYdUUrCzFq04Jg2Fwbyes46lO2zeh8Tcl6FvwsjFFK-FouBLLkTBC53JIyCGf80rB9hboa9o6K-r-g3W19rvmgof3Qg_A648kvzRZDlkIUouy4b8Z4pfzSFwjXdQibg9gf6hUmFqj7NWteuPB4bBli4pBFXSPwRtxKpKWO2PLqNKDqaYN-FIyb0OnMNArDTK4CKfT:feedlydev'

headers = {
    'Authorization': 'OAuth %s' % (ACCESS_TOKEN)
}

feedly_client = FeedlyApiClient(CLIENT_ID, ACCESS_TOKEN)

unread_urls = feedly_client.get_all_unread_article_urls()
unread_count = len(unread_urls)
print(f'Unread Count: {unread_count} articles')


NYT_URL_REGEX = '^https://www.nytimes.com'
nyt_regex_pattern = re.compile(NYT_URL_REGEX)

nyt_article_id_to_text_and_reading_time = {}
for link in unread_urls:
    print(f'Current link: {link}')
    match_obj = nyt_regex_pattern.match(link)
    if match_obj is not None:
        parser = NYTParser(article_url=link)
        try:
            article_text, reading_time = parser.get_text_and_reading_time()
            nyt_article_id_to_text_and_reading_time[parser.get_article_id()] = (article_text, reading_time)
        except TypeError:
            link_id = parser.get_article_id()
            print(f'Link not working: {link}, Link ID:{link_id}')


for key, value in nyt_article_id_to_text_and_reading_time.items():
    print(f'Article ID: {key}\n')
    print(f'Article READING TIME: {value[1]}\n')
    print(f'Article TEXT: {value[0]}\n')
