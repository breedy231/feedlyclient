import httpx
from bs4 import BeautifulSoup
from collections import defaultdict


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