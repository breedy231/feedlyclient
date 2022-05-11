import httpx
from bs4 import BeautifulSoup
import re

class AVClubParser:
    def __init__(self, article_url):
        self.article_url = article_url
        self.article_text = ''
        self.article_id = None

    def get_article_soup(self):
        response = httpx.get(self.article_url)
        article_soup = BeautifulSoup(response.content, 'html.parser')
        return article_soup

    def parse_video_links_from_html(self):
        soup = self.get_article_soup()
        video_links = []
        video_ids = []

        # Regex for getting Youtube Video ids
        pattern = re.compile(r'([a-zA-Z0-9]{11})')

        # <a> block
        all_links = soup.find_all('a')
        for link in all_links:
            link_content = link.get('href')
            if link_content and 'youtube.com/watch?v=' in link_content:
                video_links.append(link_content)
            else:
                continue

        # <iframe> block - for AV Club
        all_iframes = soup.find_all('iframe')
        for iframe in all_iframes:
            iframe_content = iframe.get('data-src')
            if iframe_content:
                video_links.append(iframe_content)
            else:
                continue

        for link in video_links:
            match = pattern.search(link)
            video_ids.append(match.group())
    
        return video_ids
        