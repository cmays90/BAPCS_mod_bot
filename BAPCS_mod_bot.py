'''
Documentation, License etc.

@package BAPCS_mod_bot
'''

import configparser
import praw
import logging

handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)
logger = logging.getLogger('prawcore')
logger.setLevel(logging.DEBUG)
logger.addHandler(handler)

path = 'config.ini'
config = configparser.ConfigParser()
config.read(path)

reddit_config = dict(config.items("reddit"))

reddit = praw.Reddit(user_agent=reddit_config['user_agent'],
                     client_id = reddit_config['client_id'],
                     client_secret = reddit_config['client_secret'],
                     username = reddit_config['username'],
                     password = reddit_config['password'])


subredditName = config.get('general', 'subreddits')
print()
print(f'Logged in as {reddit.user.me()}')

subreddit = reddit.subreddit(subredditName)

while True:
    print ("==================================\nSUBMISSIONS\n==================================\n")
    for submission in subreddit.stream.submissions(pause_after = -1):
        if submission is None:
            break
        print(submission.title)
    print ("==================================\nCOMMENTS\n==================================\n")
    for comment in subreddit.stream.comments(pause_after = -1):
        if comment is None:
            break;
        print(comment)
    print ("==================================\nINBOX\n==================================\n")    
    for msg in reddit.inbox.stream(pause_after = -1, skip_existing = True):
        if msg is None:
            break;
        print(msg)
    print ("==================================\nMODQUEUE\n==================================\n")
    for item in subreddit.mod.modqueue(limit=None, pause_after = -1):
        if item is None:
            break;
        print(item)
    print ("==================================\nMOD MESSAGES\n==================================\n")
    for message in subreddit.mod.inbox(limit=5):
        if message is None:
            break;
        print("From: {}, Body: {}".format(message.author, message.body))
        for reply in message.replies:
            print("From: {}, Body: {}".format(reply.author, reply.body))
    print ("==================================\nSPAM\n==================================\n")
    for spam in subreddit.mod.spam(pause_after = -1):
        if spam is None:
            break;
        print(item)
    
    