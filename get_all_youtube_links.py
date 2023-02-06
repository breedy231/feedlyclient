from feedly import FeedlyApiClient
import json
import os

client_id = 'ede62ec0-5773-49b1-bfe7-c2843e0f4dec'
api_key = 'AyNKhB7ptI-z90IhILxXCz5d9DNQAVN5tlHRc8AZlzswFbSBXDKzOwdfDNqKt5PsvpcRTHOaa3WbcAfuxpc9_CoRL9779oL2S5tZTqWmqGOE4Nwo17EXHx9_cbawAB6NCAt1tRLPdpTa0cv12W4mCxsdpoUHFQW4979CLu-yGFqwC749N1FM8FiM8Hsqy0-XjhcVix2WA1zSqnHQ8nTJfYG11fkeHkPhdPYjxor8FbS-CP9JS9K-5Zp2jEE4:feedlydev'
secrets_file_loc = '/Users/brendanreed/Downloads/client_secret_16111337516-fqqpsf3s2i9jvot4m66nmrg2t3q5dqo4.apps.googleusercontent.com.json'
client = FeedlyApiClient(client_id, api_key, secrets_file_loc)

youtube_links = client.get_all_youtube_links()
print(f'Got all YT Links, writing to output files. Num links: {len(youtube_links)}')

# TODO add actual date parsing for this file
output_file = open(os.getcwd() + '/outputs/10_27_22.json', 'w')
serialized_links = json.dumps(youtube_links)
output_file.write(serialized_links)
print('Wrote output to file')
    
# with open(os.getcwd() + '/outputs/10_4_22_videomap.json') as file:   
#     rewritten = {}
#     for key, value in client.VIDEOS_TO_URLS.items():
#         rewritten[key] = list(value)

#     serialized_links = json.dumps(rewritten)
#     file.write(serialized_links)
#     print('Wrout videomap to file')

# with open(os.getcwd() + '/outputs/10_4_22_duplicates.json') as file:
#     rewritten = {}
#     for key, value in client.TITLES_TO_DUPLICATES.items():
#         rewritten[key] = list(value)

#     serialized_links = json.dumps(rewritten)
#     file.write(serialized_links)
#     print('Wrout duplicates to file')