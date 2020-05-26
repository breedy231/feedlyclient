class Article:

    def __init__(self, url, feedly_id, unread=True, article_text=None):
        self.url = url
        self.feedly_id = feedly_id
        self.article_text = article_text
        self.reading_time = self.get_estimated_reading_time() if article_text is not None else 0
        self.unread = unread
        self.sent_to_pocket = False
        self.tags = []

    def mark_as_read(self):
        self.unread = False

    def add_tag(self, tag):
        self.tags = self.tags.append(tag)

    def add_tags(self, tags):
        self.tags = self.tags + tags

    def get_estimated_reading_time(self):
        WPM = 200
        num_words_in_text = len(self.article_text.split())
        estimated_reading_time = round(num_words_in_text/WPM)
        self.reading_time = estimated_reading_time
        return estimated_reading_time
