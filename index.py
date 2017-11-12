import os, json, tempfile, sys, io, urllib, requests, contextlib
from tweepy.streaming import StreamListener
from tweepy import OAuthHandler
from tweepy import Stream

from azure.storage.blob import BlockBlobService
from azure.storage.blob import ContentSettings
azure_blob_account = os.environ['azure_blob_account']
azure_blob_account_key = os.environ['azure_blob_account_key']
block_blob_service = BlockBlobService(account_name=azure_blob_account, account_key=azure_blob_account_key)

@contextlib.contextmanager
def nostdout():
    save_stdout = sys.stdout
    sys.stdout = io.BytesIO()
    yield
    sys.stdout = save_stdout

auth = OAuthHandler(os.environ['consumer_key'], os.environ['consumer_secret'])
auth.set_access_token(os.environ['access_token'], os.environ['access_token_secret'])

class TweetListener(StreamListener):
    def on_data(self, data):
        try:
            tweet = json.loads(data)
            print('Got tweet from %s "%s" (%i followers)' % (tweet['user']['screen_name'], tweet['text'], tweet['user']['followers_count']))
            if not tweet['retweeted']:
                if (tweet['extended_entities'] and tweet['extended_entities']['media']):
                    print('Got %i media item(s)' % len(tweet['extended_entities']['media']))
                    for media in tweet['extended_entities']['media']:
                        if (media['type'] == 'photo'):
                            print("Ooooo a photo")
                            image_data = urllib.urlopen(media['media_url_https']).read()

                            filename_in = tweet['id_str'] + '.jpg'
                            file_path_in = tempfile.gettempdir() + '/' + filename_in

                            with open(file_path_in, 'wb') as f:
                                f.write(image_data)

                            with nostdout():
                                block_blob_service.create_blob_from_path(
                                    os.environ['azure_blob_container'],
                                    filename_in,
                                    file_path_in,
                                    content_settings=ContentSettings(content_type='image/jpg')
                                )

                            print ("Blob upload succeeded for -> " + media['media_url_https'])
                        else:
                            print("Not a photo :(")
                else:
                    print('No media :(')
            else:
                print("Oh... a retweet")
        except Exception as e:
            print("error oops", e)

    def on_error(self, status):
        print('Error from tweet streamer', status)

if __name__ == '__main__':
    print('Setting up')
    l = TweetListener()
    stream = Stream(auth, l)

    print('Listening for tweets')
    stream.filter(track=['@retromebot'])
