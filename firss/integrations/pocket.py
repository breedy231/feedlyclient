import httpx

class PocketApiClient:

    MAIN_URL = 'https://getpocket.com/v3/'

    AUTH_URL = MAIN_URL + 'oauth/request'