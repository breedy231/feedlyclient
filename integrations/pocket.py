import httpx

class PocketApiClient:
    MAIN_URL = 'https://getpocket.com/v3/'
    ADD_URL = self.MAIN_URL + 'add'

    def __init__(self, client_id, access_token):
        self.client_id = client_id,
        self.access_token = access_token

    def _send_request(self, url, request_data=None):
        auth_data = {
            'client_id': self.client_id,
            'access_token': self.access_token
        }

        if request_data is not None:
            full_data = {**request_data, **auth_data}
            response = httpx.post(url, data=request_data)
        else:
            response = httpx.post(url, data=auth_data)
        return response


    def add_item(self, url, title=None, tags=None, tweet_id=None):
        if any(tweet_id, tags, tweet_id) is True:
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

        return bool(response['status'])



