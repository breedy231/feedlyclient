"""
A Client for interacting with the FeedlyAPI. 

Main class: 
    - FeedlyAPIClient
"""
# pylint: disable=E1101
from collections import defaultdict
import json
import os
import re
from typing import List, Optional, Tuple

from bs4 import BeautifulSoup
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
import httpx
from tqdm import tqdm

YOUTUBE_URL = 'https://www.youtube.com/watch?v='
MAIN_URL = 'https://cloud.feedly.com'
STREAM_CONTENTS_URL = MAIN_URL + '/v3/streams/contents?streamId='
MARKERS_URL = MAIN_URL + '/v3/markers'
SINGLE_REQUEST_ITEM_SIZE = 20

REGEX_STRINGS = (
    r'^.*([a-zA-z0-9]{11}).*$',
    r'^.*([a-zA-Z0-9]{8}-[a-zA-Z0-9}]{2}).*$',
    r'.*([a-zA-z0-9]{4}-[a-zA-z0-9]{6}).*',
    r'.*\/([a-zA-z0-9]{11})\?.*',
    r'.*\/([a-zA-z0-9]{11}).*',
    r'.*youtube-video-([a-zA-Z0-9]*-[a-zA-Z0-9]*)\&.*',
)
VERGE_REGEX = re.compile(r'.*\/([a-zA-z0-9]{11}).*')


REGEXES = [re.compile(regex_string) for regex_string in REGEX_STRINGS]


class BadYoutubeLink(Exception):
    """
        Exception for a poorly formatted YouTube link, from a bad regex match. 
    """


class FeedlyApiClient:
    """
    Client to interact with the Feedly API
    """
    # YOUTUBE STUFF
    # Disable OAuthlib's HTTPS verification when running locally.
    # *DO NOT* leave this option enabled in production.
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
    API_SERVICE_NAME = "youtube"
    API_VERSION = "v3"
    SCOPES = ["https://www.googleapis.com/auth/youtube.force-ssl"]
    VIDEOS_TO_URLS = defaultdict(set)

    def __init__(self, client_id, api_key, secrets_file_loc, playlist_id):
        """
        Initialize the Feedly Client. 

        Args: 
            client_id: The user ID returned from Feedly. 
            api_key: The API key returned from Feedly. 
            secrets_file_location: The location on your machine of the secrets file
                from the Google API console, for saving videos to YouTube. 
            playlist_id: The playlist ID to save videos to. 

        Returns: 
            The initialized client. 
        """
        self.client_id = client_id
        self.api_key = api_key
        self.unread_article_count = 0
        self.article_map = defaultdict(str)
        self.secrets_file = secrets_file_loc
        self.playlist_id = playlist_id
        self.api_headers = {
            'Authorization': f'OAuth {self.api_key}'
        }

    def global_stream(self, unread=Optional[bool]) -> str:
        """
        Get the global stream for the user. Optionally include flag to only get unread articles. 

        Args: 
            unread: Optional argument to only get unread articles in the stream URL. 
                Defaults to None. 

        Returns: 
            The global stream URL for the user. 
        """
        return (
            STREAM_CONTENTS_URL + f'user/${self.client_id}/category/global.all'
            + ('&unreadOnly=true' if unread else '')
        )

    def get_url_response_content(self, url: str) -> dict:
        """
        Make an authorized GET request to the input URL. 

        Args: 
            url: The input URL. 

        Returns: 
            JSON-loaded response data. 
        """
        response = httpx.get(url, headers=self.api_headers)
        response_content = json.loads(response.content)
        return response_content

    def post_url_response_content(self, url: str, payload=Optional[dict]) -> int:
        """
        Make an authorized POST request to the input URL, with optional input data. 

        Args: 
            url: The input URL.
            payload: JSON data. Optional. 

        Returns: 
            The response status code. 
        """
        response = httpx.post(url, headers=self.api_headers, json=payload)
        return response.status_code

    def get_all_unread_articles(self, url=Optional[str], article_agg=Optional[List]):
        """
        Gets all unread articles from Feedly for the authorized user. 
        If there is a continuation in the initial response, recur until exhausted. 

        Args: 
            url: The string to use in the request. Defaults to the user's personal unread stream. 
            article_agg: The unread articles from the user's personal unread stream. 
                Defaults to an empty list. 

        Returns: 
            A list of article objects, for all of the unread articles in the user's 
            personal unread steam. 
        """
        request_url = url if url is not None else self.global_stream(
            unread=True
        )
        response_content = self.get_url_response_content(request_url)
        continuation = response_content.get('continuation', None)
        response_items = response_content['items']
        num_items = len(response_items)

        if num_items == SINGLE_REQUEST_ITEM_SIZE and continuation is not None:
            continuation_url = self._make_continuation_url(continuation)
            new_agg = article_agg + response_items
            return self.get_all_unread_articles(url=continuation_url, article_agg=new_agg)

        result_agg = article_agg + response_content['items']
        print(
            f'Finished getting unread articles; Total length:{len(result_agg)}')
        return result_agg

    def _make_continuation_url(self, continuation: str) -> str:
        """
        Make the continuation URL for the Feedly API. 

        Args: 
            continuation: The marker to use in the continuation url. 

        Returns: 
            The full continuation URL to use in the response. 
        """
        url_to_continue = self.global_stream(unread=True)
        return url_to_continue + '&continuation=' + continuation

    def get_links_and_unread_map(self) -> dict:
        """
        Get the map of article URL to ID. 

        Returns: 
            A dictionary of article URLs to article ID
        """
        article_url_to_id = {}
        unread_articles = self.get_all_unread_articles()

        for article in unread_articles:
            try:
                main_article_link = article['alternate'][0]['href']
                article_url_to_id[main_article_link] = article['id']
            except KeyError:
                continue

        return article_url_to_id

    def get_all_youtube_links(self) -> Tuple[List[str], List[str]]:
        """
        Gets all YouTube links present in unread articles for the authorized client user. 

        Returns: 
            A tuple of lists of strings, the first containing Youtube links and the second
            containing Feedly article IDs. 
        """
        result_youtube_links = set()
        all_read_articles = []

        possible_read_articles = self.get_links_and_unread_map()

        for link, article_id in tqdm(list(possible_read_articles.items())):
            result_videos = []

            try:
                response = httpx.get(link)
            except httpx.ReadTimeout:
                print(f'Read timeout for link: {link}')

            soup = BeautifulSoup(response.content, 'html.parser')

            if 'verge' in link:
                result_videos = self._get_verge_youtube_ids(soup, VERGE_REGEX)

            external_links = [link.get('href') for link in soup.find_all('a')]
            other_links = [hyper.get('data-src')
                           for hyper in soup.find_all('iframe')]
            other_other_links = [hyper.get('src')
                                 for hyper in soup.find_all('iframe')]

            if len(external_links) > 0:
                result_videos.extend(
                    video for video in external_links
                    if video is not None and self._link_has_video(video)
                )

            if len(other_links) > 0:
                result_videos.extend(self._get_avclub_youtube_ids(
                    other_links, REGEXES))

            if len(other_other_links) > 0:
                result_videos.extend(self._get_avclub_youtube_ids(
                    other_other_links, REGEXES))

            if len(
                [url for url in result_videos if 'v=ideo' in url]
            ) > 0:
                raise BadYoutubeLink(
                    f'Bad YT Video links found for link {link}. {result_videos}'
                )

            result_youtube_links.update(result_videos)
            all_read_articles.append(article_id)

        return list(result_youtube_links), list(all_read_articles)

    def _get_verge_youtube_ids(self, soup: BeautifulSoup, regex: re.Pattern):
        """
        Gets the YouTube video IDs from Verge links. 

        Args: 
            links: A list of URLs to check. 
            strings_to_match: A list of regexes to match against. 

        Returns: 
            A list of YouTube video links. 
        """
        data_script = soup.find_all('script')[-1]
        loaded_script = json.loads(data_script.text)
        all_videos = []
        try:
            lead_component = loaded_script['props']['pageProps']['hydration'][
                'responses'][0]['data']['entity']['leadComponent']
            page_components = loaded_script['props']['pageProps']['hydration'][
                'responses'][0]['data']['entity']['body']['components']
            all_components = [lead_component] + page_components
            for page_component in all_components:
                if (
                    page_component['__typename'] == 'EntryBodyEmbed'
                    or page_component['__typename'] == 'EntryLeadEmbed'
                ):
                    embed_html = page_component['embed']['embedHtml']
                    is_match = regex.match(embed_html)
                    if is_match:
                        watch_link = f"{YOUTUBE_URL}{is_match.groups()[0]}"
                        all_videos.append(watch_link)
            return all_videos
        except KeyError:
            return all_videos

    def _get_avclub_youtube_ids(
        self,
        links: List[str],
        strings_to_match: List[re.Pattern]
    ) -> List[str]:
        """
        Gets the YouTube video IDs from AV Club links. 

        Args: 
            links: A list of URLs to check. 
            strings_to_match: A list of regexes to match against. 

        Returns: 
            A list of YouTube video links. 
        """
        videos = []
        filtered_links = [
            item for item in links if item is not None and 'google' not in item]
        for link in filtered_links:
            for string in strings_to_match:
                is_match = string.match(link)
                if is_match and 'ideo-' not in is_match.groups()[0]:
                    watch_link = f"{YOUTUBE_URL}{is_match.groups()[0]}"
                    videos.append(watch_link)
                    break
        return videos

    def _link_has_video(self, url: str) -> bool:
        """
        Determines if a given link contains a video, i.e. is hosted on YouTube or Vimeo.

        Args: 
            url: The URL to check. 

        Returns: 
            True or False, whether or not the input URL is a video. 
        """
        return 'www.youtube.com/watch?v=' in url or 'vimeo' in url

    def add_video_to_playlist(self, video_id: str):
        """
        Add input video to a playlist on YouTube

        Args: 
            video_id: The video ID to add to the playlist

        Returns
            The API response.
        """
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
                    "playlistId": self.playlist_id,
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

    def mark_articles_as_read(self, article_ids: List[str]) -> int:
        """
        Marks input articles as read for the authorized user

        Args: 
            article_ids: A list of article IDs. 

        Returns:
            The response status code. 
        """
        request_url = MARKERS_URL
        payload = {
            "action": "markAsRead",
            "type": "entries",
            "entryIds": article_ids,
        }
        response_status = self.post_url_response_content(request_url, payload)
        return response_status
