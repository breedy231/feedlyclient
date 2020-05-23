from bs4 import BeautifulSoup
from collections import defaultdict
import httpx
import json
import re


CLIENT_ID = 'ede62ec0-5773-49b1-bfe7-c2843e0f4dec'
ACCESS_TOKEN = 'Azps7uUKhDZwbAVqhVZI27kviVz0bb7709m0GJF6OsA0DWppd-zzgCnUYdUUrCzFq04Jg2Fwbyes46lO2zeh8Tcl6FvwsjFFK-FouBLLkTBC53JIyCGf80rB9hboa9o6K-r-g3W19rvmgof3Qg_A648kvzRZDlkIUouy4b8Z4pfzSFwjXdQibg9gf6hUmFqj7NWteuPB4bBli4pBFXSPwRtxKpKWO2PLqNKDqaYN-FIyb0OnMNArDTK4CKfT:feedlydev'

headers = {
    'Authorization': 'OAuth %s' % (ACCESS_TOKEN)
}

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

    def get_url_response_content(self, url):
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

    def get_all_unread_articles(self, url, article_agg=[]):
        response_content = self.get_url_response_content(url)
        continuation = response_content.get('continuation', None)

        if len(response_items) == 20:
            continuation_url = url + 'continuation=' + continuation
            response_content = self.get_url_response_content(continuation_url)

            article

            return

        if continuation is not None:
            continuation_url = url + 'continuation=' + continuation
            article_agg.append(response_content['items'])
            self.get_all_unread_articles(continuation_url, article_agg)
        else:
            return article_agg

    def get_all_unread_article_urls(self):
        unread_articles = self.get_all_unread_articles()
        urls = []
        for unread_article in unread_articles:
            urls.append(unread_article['alternate'][0]['href'])
        return urls


class NYTParser:
    def __init__(self, article_url):
        self.article_url = article_url
        self.article_text = ''
        self.article_id = None

    def get_article_soup(self):
        response = httpx.get(self.article_url)
        article_soup = BeautifulSoup(response.content, 'html.parser')
        return article_soup

    def get_article_id(self):
        soup = self.get_article_soup()
        article_id = soup.find_all(attrs={'name':'articleid'})[0]['content']
        return article_id

    def get_article_content(self):
        soup = self.get_article_soup()
        article_section = soup.find(attrs={'name':'articleBody'})
        return article_section

    def get_text_divs(self, article):
        divs_dict = defaultdict(list)
        for index, section in enumerate(article.contents):
            if section.name == 'div' and len(section.contents) > 0:
                divs_dict[index] = section

        return divs_dict

    def combine_article_text(self, article_dict):
        article_text = ''
        for index, section in article_dict.items():
            if index == 1:
                article_text = article_text + section.contents[0].contents[0].contents[0] + ' '
            elif section.has_attr('data-testid'):
                continue
            else:
                article_text = article_text + section.contents[0].contents[0].contents[0]

        return article_text

    def get_estimated_reading_time(self, full_text):
        WPM = 200
        num_words_in_text = len(full_text.split())
        estimated_reading_time = round(num_words_in_text/WPM)
        return 'Estimate reading time: %s minutes' % str(estimated_reading_time)

    def get_text_and_reading_time(self):
        article_content = self.get_article_content()
        article_text_divs = self.get_text_divs(article_content)
        article_full_text = self.combine_article_text(article_text_divs)
        article_estimated_reading_time = self.get_estimated_reading_time(article_full_text)
        return article_full_text, article_estimated_reading_time


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
