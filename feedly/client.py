import httpx
import json
from bs4 import BeautifulSoup
from collections import defaultdict
from uuid import uuid4

class FeedlyApiClient:
    MAIN_URL = 'https://cloud.feedly.com'

    PROFILE_URL = MAIN_URL + '/v3/profile'
    SUBSCRIPTIONS_URL = MAIN_URL + '/v3/subscriptions'
    COLLECTIONS_URL = MAIN_URL + '/v3/collections'
    UNREAD_COUNTS_URL = MAIN_URL + '/v3/markers/counts'
    STREAM_CONTENTS_URL = MAIN_URL + '/v3/streams/contents?streamId='

    PERSONAL_ALL_UNREAD_FEED_ID = STREAM_CONTENTS_URL + 'user/ede62ec0-5773-49b1-bfe7-c2843e0f4dec/category/global.all'
    PERSONAL_ALL_UNREAD_STREAM = STREAM_CONTENTS_URL + 'user/ede62ec0-5773-49b1-bfe7-c2843e0f4dec/category/global.all&unreadOnly=true'

    def __init__(self, client_id, api_key):
        self.client_id = client_id
        self.api_key = api_key
        self.unread_article_count = None
        self.article_map = defaultdict(str)

    def get_url_response_content(self, url):
        headers = {
            'Authorization': 'OAuth %s' % (self.api_key)
        }
        response = httpx.get(url, headers=headers)
        response_content = json.loads(response.content)
        return response_content

    def get_all_unread_feeds(self):
        response_content = self.get_url_response_content(UNREAD_COUNTS_URL)
        unread_feeds = []
        for feed in response_content['unreadcounts']:
            if feed['count'] > 0 and feed['id'][:4] == 'feed':
                unread_feeds.append(feed['id'])

        return unread_feeds

    def get_unread_feed_url(self, feed_id):
        return STREAM_CONTENTS_URL % feed_id + '?unreadOnly=true'

    def get_all_unread_articles(self, url=None, article_agg=[]):
        if url is None:
            response_content = self.get_url_response_content(self.PERSONAL_ALL_UNREAD_STREAM)
        else:
            response_content = self.get_url_response_content(url)

        continuation = response_content.get('continuation', None)
        response_items = response_content['items']
        num_items = len(response_items)
        if num_items == 20 :
            if url is not None:
                continuation_url = url + '&continuation=' + continuation
            else:
                continuation_url = self.PERSONAL_ALL_UNREAD_STREAM + '&continuation=' + continuation

            new_agg = article_agg + response_items
            return self.get_all_unread_articles(url=continuation_url, article_agg=new_agg)
        else:
            new_agg = article_agg + response_content['items']
            return new_agg

    def set_unread_count(self, unread_count):
        self.unread_article_count = unread_count

    def get_new_id(self):
        return uuid4()

    def get_estimated_reading_time(self, full_text):
        WPM = 200
        num_words_in_text = len(full_text.split())
        estimated_reading_time = round(num_words_in_text/WPM)
        return 'Estimate reading time: %s minutes' % str(estimated_reading_time)

    def get_all_unread_article_urls(self):
        unread_articles = self.get_all_unread_articles()
        self.set_unread_count(len(unread_articles))
        urls = []
        for unread_article in unread_articles:

            feed_content = unread_article.get('content', None)

            if feed_content is not None:
                article_content = feed_content.get('content', None)
                article_soup = BeautifulSoup(article_content, 'html.parser')
                rough_article_text = article_soup.text.rstrip()
                rough_article_length = len(rough_article_text)
                # article_id = str(self.get_new_id())
                estimated_reading_time = self.get_estimated_reading_time(rough_article_text)
                self.article_map[unread_article['alternate'][0]['href']] = (rough_article_text, estimated_reading_time)
                urls.append(unread_article['alternate'][0]['href'])
            else:
                self.article_map[self.get_new_id()] = 'No Content Available'
        return urls