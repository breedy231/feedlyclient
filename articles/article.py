class Article:

    def __init__(self, url, feedly_id, unread=True, article_text=None):
        self.url = url
        self.feedly_id = feedly_id
        self.article_text = article_text
        self.reading_time = self.get_estimated_reading_time()
        self.unread = unread
        self.sent_to_pocket = False

    def mark_as_read(self):
        self.unread = False

    def get_estimated_reading_time(self):
        WPM = 200
        num_words_in_text = len(self.article_text.split())
        estimated_reading_time = round(num_words_in_text/WPM)
        self.reading_time = estimated_reading_time
        return estimated_reading_time
