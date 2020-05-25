class Article:

    def __init__(self, url, feedly_id, unread=True, article_text=None, reading_time=0):
        self.url = url
        self.feedly_id = feedly_id
        self.reading_time = reading_time
        self.unread = unread
        self.article_text = article_text
        self.sent_to_pocket = False

    def mark_as_read(self):
        self.unread = False
