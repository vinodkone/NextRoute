import time
import tweepy

consumer_key = 'FKirArdIkcVQv7ODmjJPAw'
consumer_secret = 'aDDces1zYAHpZiMn9fjC1EOWaOY60Jzg0vQDBv4F0M'

access_token = '436462576-iz26BYOlXzr6y956pwdtMxkycuOp873LYm1hVwyG'
access_token_secret = 'F7usln20pFYiA9NAe2e47SCCIwUraYUw7EN82SOaW4'

class StreamListener(tweepy.StreamListener):

  def on_status(self, status):
    print 'Received status: %s from user: %s coord: %s' \
      % (status.text, status.author.screen_name, status.coordinates)

  def on_error(self, status_code):
    print 'An error has occured: %s' % status_code
    return True

  def on_timeout(self):
    print 'Timed out!'

  def main(self):
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)

    stream = tweepy.Stream(auth, self, retry_count=2)

    while True:
      print 'Starting the user stream'
      stream.userstream()
      time.sleep(5)

if __name__ == "__main__":
  try:
    StreamListener().main()
  except KeyboardInterrupt:
      pass
