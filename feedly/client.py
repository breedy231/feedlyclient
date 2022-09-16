from sys import api_version
import httpx
import json
from tqdm import tqdm
from bs4 import BeautifulSoup
from collections import defaultdict
from uuid import uuid4

import os

import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors

from articles import Article


# TODO integrate article parsers 
# TODO mark article as read in feedly after parsing video link & sending to Youtube
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

    # YOUTUBE STUFF

    # Disable OAuthlib's HTTPS verification when running locally.
    # *DO NOT* leave this option enabled in production.
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
    API_SERVICE_NAME = "youtube"
    API_VERSION = "v3"
    SCOPES = ["https://www.googleapis.com/auth/youtube.force-ssl"]

    def __init__(self, client_id, api_key, secrets_file_loc):
        self.client_id = client_id
        self.api_key = api_key
        self.unread_article_count = 0
        self.article_map = defaultdict(str)
        self.secrets_file = secrets_file_loc

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
        
        if num_items == self.SINGLE_REQUEST_ITEM_SIZE and continuation is not None:
            continuation_url = self._make_continuation_url(continuation, url)
            new_agg = article_agg + response_items
            return self.get_all_unread_articles(url=continuation_url, article_agg=new_agg)
        else:
            result_agg = article_agg + response_content['items']
            print(f'Finished getting unread articles; Total length:{len(result_agg)}')
            return result_agg

    def _make_continuation_url(self, continuation, url=None):
        url_to_continue = self.PERSONAL_ALL_UNREAD_STREAM
        continuation_url = url_to_continue + '&continuation=' + continuation 
        return continuation_url

    def set_unread_count(self, unread_count):
        self.unread_article_count = unread_count

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
            article_obj = Article(url, feed_id, article_text=parsed_text)
        else:
            article_obj = Article(url, feed_id)
        return article_obj

    def get_all_long_articles(self):
        result = []
        for article_obj in self.article_map.values():
            if article_obj.reading_time >= 5:
                result.append(article_obj)
        return result

    def get_all_youtube_links(self):
        external_links = []
        all_youtube_links = set()

        unread_articles = self.get_all_unread_articles()
        all_links = [item['alternate'][0]['href'] for item in unread_articles]

        for link in tqdm(all_links):
            response = httpx.get(link)
            soup = BeautifulSoup(response.content, 'html.parser')
            external_links = external_links + [link.get('href') for link in soup.find_all('a')]
            if len(external_links) > 0:
                result_links = [video for video in external_links if video is not None and 'www.youtube.com/watch?v=' in video]
                all_youtube_links.update(result_links)

        return list(all_youtube_links)

    def add_video_to_playlist(self, video_id: str):
         # Get credentials and create an API client
        flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
            self.secrets_file, 
            self.SCOPES
        )
        credentials = flow.run_console()
        youtube = googleapiclient.discovery.build(
            self.API_SERVICE_NAME, 
            self.API_VERSION, 
            credentials=credentials
        )
        request = youtube.playlistItems().insert(
            part="snippet",
            body={
            "snippet": {
                "playlistId": "PLx0ErPjtWhPuMEgM3R9anuaO-gBYw4UK5",
                "position": 0,
                "resourceId": {
                "kind": "youtube#video",
                "videoId": video_id
                }
            }
            }
        )
        response = request.execute()
        return response