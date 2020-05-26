import httpx
import json

class PocketApiClient:
    MAIN_URL = 'https://getpocket.com/v3/'
    ADD_URL = MAIN_URL + 'add'
    SEND_URL = MAIN_URL + 'send'
    RETRIEVE_URL = MAIN_URL + 'get'
    AUTH_URL = MAIN_URL + 'oauth/request'

    def __init__(self, client_id):
        self.client_id = client_id
        self.access_token = None

    def _send_request(self, url, request_data=None):
        auth_data = {
            'consumer_key': self.client_id,
            'access_token': self.access_token
        }

        headers = {
            'Content-Type': 'application/json'
        }

        if request_data is not None:
            full_data = {**request_data, **auth_data}
            response = httpx.post(url, json=full_data, headers=headers)
        else:
            response = httpx.post(url, json=auth_data, headers=headers)
        return response

    def get_unread_items(self):
        # request_data = {
        #     'state': 'unread',
        #     'sort': 'newest',
        #     'detailType': 'simple'
        # }
        # response = self._send_request(self.RETRIEVE_URL, request_data=request_data)
        response = self._send_request(self.RETRIEVE_URL)
        return bool(response.content['status'])


    def add_item(self, url, title=None, tags=None, tweet_id=None):
        if any((tweet_id, tags, tweet_id)) is True:
            request_data = {}

            if title is not None:
                request_data['title'] = title
            if tags is not None:
                request_data['tags'] = tags
            if tweet_id is not None:
                request_data['tweet_id'] = tweet_id

            response = self._send_request(url, request_data=request_data)
        else:
            response = self._send_request(url)

        return bool(response.content['status'])

    def add_items(self, articles):
        items = []
        for article in articles:
            article_dict = {}

            if len(article.tags) > 0:
                article_dict['tags'] = article.tags

            article_dict['url'] = article.url
            items.append(article_dict)

        request_data = {
            'actions': items
        }

        response = self._send_request(self.SEND_URL, request_data=request_data)
        return bool(response['status'])

    def get_access_token(self):
        request_data = {
            'consumer_key': self.client_id,
            'redirect_uri': 'localhost:1234'
        }

        response = httpx.post(self.AUTH_URL, json=request_data)
        response_text = response.text
        access_token = response_text.split("code=")[1]
        self.access_token = access_token
        return access_token


CLIENT_ID = '91578-937994cb753e2e7f663e36d3'
client = PocketApiClient(CLIENT_ID)
access_token = client.get_access_token()
response = client.get_unread_items()
print(response)