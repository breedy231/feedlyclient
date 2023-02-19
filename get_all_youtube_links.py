from feedly import FeedlyApiClient
import json
import os

client_id = 'ede62ec0-5773-49b1-bfe7-c2843e0f4dec'
api_key = 'A9Ji62JsCRIVExizJZM-DI1Mwkof57WfXEWVhbRgAyJKLMbN1JUeK_0IREx5IobO0eivsJqenMFKj-jsRgzoHvzahfreAuStFfavhn8Bu-iJBQADVbIXzlhDpFg4-O18ER3xpWnO8kzkwiVo_thb-gzzvUIWIqovvWFCZfwQlbj6qJPiqB4Gfmp3qCGXEtywFDaam4ZNmVSCb-HB15Y5Gri1yUSkeVgshSBrS_EMQrY3eKA-QOqrFc6Tk_CqzA:feedlydev'
secrets_file_loc = '/Users/brendanreed/Downloads/client_secret_16111337516-fqqpsf3s2i9jvot4m66nmrg2t3q5dqo4.apps.googleusercontent.com.json'
client = FeedlyApiClient(client_id, api_key, secrets_file_loc)

youtube_links, read_article_ids = client.get_all_youtube_links()
print(f'Got all YT Links, writing to output files. Num links: {len(youtube_links)}')

# TODO add actual date parsing for this file
output_file = open(os.getcwd() + '/outputs/2_18_23.json', 'w')
serialized_links = json.dumps(youtube_links)
output_file.write(serialized_links)
print('Wrote output to file')

# print('Saving videos to Scraper playlist')
# for video in youtube_links:
#     # TODO fix needing to auth on each video save
#     response = client.add_video_to_playlist(video.split('=')[1])
# print('Finished saving videos to playlist')

print('Marking articles as read in Feedly')
response = client.mark_articles_as_read(read_article_ids)
print('Finished marking articles as read in Feedly')
