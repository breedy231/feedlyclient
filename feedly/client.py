import httpx
import json
from bs4 import BeautifulSoup
from collections import defaultdict
from uuid import uuid4

from articles import Article

class FeedlyApiClient:
    MAIN_URL = 'https://cloud.feedly.com'

    PROFILE_URL = MAIN_URL + '/v3/profile'
    SUBSCRIPTIONS_URL = MAIN_URL + '/v3/subscriptions'
    COLLECTIONS_URL = MAIN_URL + '/v3/collections'
    UNREAD_COUNTS_URL = MAIN_URL + '/v3/markers/counts'
    STREAM_CONTENTS_URL = MAIN_URL + '/v3/streams/contents?streamId='

    PERSONAL_ALL_UNREAD_FEED_ID = STREAM_CONTENTS_URL + 'user/ede62ec0-5773-49b1-bfe7-c2843e0f4dec/category/global.all'
    PERSONAL_ALL_UNREAD_STREAM = STREAM_CONTENTS_URL + 'user/ede62ec0-5773-49b1-bfe7-c2843e0f4dec/category/global.all&unreadOnly=true'

    SINGLE_REQUEST_ITEM_SIZE = 20

    def __init__(self, client_id, api_key):
        self.client_id = client_id
        self.api_key = api_key
        self.unread_article_count = 0
        self.article_map = defaultdict(str)

    def get_url_response_content(self, url):
        headers = {
            'Authorization': 'OAuth %s' % (self.api_key)
        }
        response = httpx.get(url, headers=headers)
        response_content = json.loads(response.content)
        return response_content

    def get_all_unread_articles(self, url=None, article_agg=[]):
        request_url = url if url is not None else self.PERSONAL_ALL_UNREAD_STREAM
        response_content = self.get_url_response_content(request_url)
        continuation = response_content.get('continuation', None)
        response_items = response_content['items']
        num_items = len(response_items)

        if num_items == self.SINGLE_REQUEST_ITEM_SIZE:
            continuation_url = self._make_continuation_url(continuation, url)
            new_agg = article_agg + response_items
            return self.get_all_unread_articles(url=continuation_url, article_agg=new_agg)
        else:
            result_agg = article_agg + response_content['items']
            return result_agg

    def _make_continuation_url(self, continuation, url=None):
        continuation_url = (
            url + '&continuation=' + continuation if url is not None else self.PERSONAL_ALL_UNREAD_STREAM + '&continuation=' + continuation
        )
        return continuation_url

    def set_unread_count(self, unread_count):
        self.unread_article_count = unread_count

    def get_estimated_reading_time(self, full_text):
        WPM = 200
        num_words_in_text = len(full_text.split())
        estimated_reading_time = round(num_words_in_text/WPM)
        return estimated_reading_time

    def get_all_unread_article_urls(self):
        unread_articles = self.get_all_unread_articles()
        self.set_unread_count(len(unread_articles))
        urls = []
        for unread_article in unread_articles:
            article_url = unread_article['alternate'][0]['href']
            feed_id = unread_article.get('id')
            feed_content = unread_article.get('content', None)
            article_obj = self.create_article_obj(article_url, feed_id, feed_content)
            self.add_to_article_map(article_url, article_obj)
            urls.append(article_url)
        return urls

    def add_to_article_map(self, article_url, article_obj):
        self.article_map[article_url] = article_obj

    def parse_feed_text(self, feed_content):
        article_content = feed_content.get('content', None)
        article_soup = BeautifulSoup(article_content, 'html.parser')
        rough_article_text = article_soup.text
        no_whitespace_text = rough_article_text.replace('\n', ' ')
        split_text = no_whitespace_text.split()
        joined_text = ' '.join(split_text)
        return joined_text

    def create_article_obj(self, url, feed_id, feed_content=None):
        if feed_content is not None:
            parsed_text = self.parse_feed_text(feed_content)
            rough_article_length = len(parsed_text)
            article_id = feed_content.get('id')
            estimated_reading_time = self.get_estimated_reading_time(parsed_text)
            article_obj = Article(url, feed_id, article_text=parsed_text, reading_time=estimated_reading_time)
        else:
            article_obj = Article(url, feed_id)
        return article_obj

    def get_all_long_articles(self):
        result = []
        for article_obj in self.article_map.values():
            if article_obj.reading_time >= 5:
                result.append(article_obj)
        return result
