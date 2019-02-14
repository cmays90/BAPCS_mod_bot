'''
Documentation, License etc.

@package BAPCS_mod_bot
'''

import configparser
import praw

path = 'config.ini'
config = configparser.ConfigParser()
config.read(path)

reddit_config = dict(config.items("reddit"))

reddit = praw.Reddit(user_agent=reddit_config['user_agent'],
                     client_id = reddit_config['client_id'],
                     client_secret = reddit_config['client_secret'],
                     username = reddit_config['username'],
                     password = reddit_config['password'])


print(config.get('general', 'subreddits'))
print(f'Logged in as {reddit.user.me()}')