import datetime
import pprint
import string
import time
import tweepy

from nextbus import NextBus
from tweepy.error import TweepError
from tweepy.models import Status, DirectMessage
from tweepy.utils import import_simplejson

json = import_simplejson()


# NOTE: Fill these with your application's creds 
consumer_key = ''
consumer_secret = ''

access_token = ''
access_token_secret = ''

class StreamWatcher(tweepy.StreamListener):

  def on_data(self, data):
    """Called when raw data is received from connection.

    Override this method if you wish to manually handle
    the stream data. Return False to stop stream and close connection.
    """

    if 'in_reply_to_status_id' in data:
      status = Status.parse(self.api, json.loads(data))
      return self.on_status(status)
    elif 'delete' in data:
      delete = json.loads(data)['delete']['status']
      if self.on_delete(delete['id'], delete['user_id']) is False:
        return False
    elif 'limit' in data:
        if self.on_limit(json.loads(data)['limit']['track']) is False:
          return False
    elif 'sender_id' in data and 'recipient_id' in data:
      dm = DirectMessage.parse(self.api, json.loads(data))
      return self.on_dm(dm)
    elif 'event' in data and 'follow' in data:
      content = json.loads(data)
      if 'event' in content and content['event'] == 'follow':
        return self.on_follow(content)

  def on_dm(self, dm):
    try:
      print 'Received DM: %s from: %s' % (dm.direct_message['text'],
                                          dm.direct_message['sender']['screen_name'])
      self.process_dm(dm)
    except Exception as e:
      print 'Exception processing dm: %s' % e

  def on_follow(self, content):
    try:
      source = content['source']['id']
      target = content['target']['id']
      print 'Received follow event from: %s to: %s' % (source, target)
      self.process_follow(source, target)
    except Exception as e:
      print 'Exception processing follow event :%s' % e

  # Over-ridden methods from StreamListener
  def on_status(self, status):
    try:
      print 'Received status: %s from %s' % (status.text, status.author.screen_name)
      self.process_status(status)
    except Exception as e:
      print 'Exception processing status: %s' % e

  def on_error(self, status_code):
    print 'An error has occurred: %s' % status_code
    return True

  def on_timeout(self):
    print 'Timed out!'


class NextRoute(StreamWatcher):

  def __init__(self):
    super(NextRoute, self).__init__()

    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)

    # Open a handle to the REST API
    self.api = tweepy.API(auth)
    self.api.retry_count = 2
    self.api.retry_delay = 5

    me = self.api.me()
    self.my_id = me.id
    self.my_name = me.screen_name
    print 'Name: %s id: %s' % (self.my_name, self.my_id)

    # Open a handle to the UserStreams API
    self.stream = tweepy.Stream(auth, self, retry_count=2)

    # Open a handle to NextBus API
    self.next_bus = NextBus()

  def run(self):
    while True:
      print 'Connecting to the user stream'
      try:
        self.stream.userstream()
      except Exception as e:
        print 'Exception from userstream %s' % e
      time.sleep(5)

  def process_follow(self, source, target):
    # If target is me, follow the source
    if target == self.my_id:
      print 'Creating friendship with: %s' % source
      self.api.create_friendship(source)

  def send_info(self, user, text, reply_to_id=None):
    # If the recipient is a follower send a DM, else send a tweet
    if self.api.exists_friendship(user, self.my_name):
      self.send_dm(user, text)
    else:
      self.send_tweet(user, text, reply_to_id)

  def send_dm(self, user, text):
    print 'Sending DM to user: %s text: %s' % (user, text)
    try:
      text = text[:140] # truncate the message to 140
      self.api.send_direct_message(user=user, text=text)
    except TweepError as e:
      print 'Exception sending DM: %s' % e.reason

  def send_tweet(self, user, text, reply_to_id):
    print 'Sending tweet @%s %s' % (user, text)
    try:
      text = '@%s %s' % (user, text)
      text = text[:140] # truncate the message to 140
      self.api.update_status(status=text, in_reply_to_status_id=reply_to_id)
    except TweepError as e:
      print 'Exception sending tweet: %s' % e.reason

  def process_dm(self, dm):
    text = dm.direct_message['text']
    user = dm.direct_message['sender']['screen_name']

    if user.upper() == 'NEXTROUTE':
      print 'Ignoring sent DM: %s' % text
      return

    self.process_info(text, user)

  def process_status(self, status):
    text = status.text
    user = status.author.screen_name
    coordinates = status.coordinates
    tweet_id = status.id

    if not text.upper().startswith('@NEXTROUTE'):
      print 'Ignoring non reply tweet: %s' % text
      return

    text = ' '.join(text.split()[1:])
    self.process_info(text, user, coordinates, tweet_id)

  def process_info(self, text, user, coordinates=None, tweet_id=None):
    print "Text: %s Coord: %s from user: %s" % (text, coordinates, user)

    if coordinates:
      coords = coordinates['coordinates']
      coords.reverse()
      resp = self.arrival_time(text, coords)
    else:
      resp = self.arrival_time(text)

    if not resp:
        resp = 'No prediction data available! for %s' % text

    self.send_info(user, resp, tweet_id)

  def arrival_time(self, text, point=None):
    # Parse the text
    words = text.split()

    if len(words) < 1:
      return "Invalid format! Please include route: %s" % text

    # Get the route
    route = string.upper(words[0])

    # Check if street information is provided
    if len(words[1:]) > 0:
      cross_street = ' '.join(words[1:])
      return self.next_bus.get_arrival_time_xstreet(route, cross_street)
    elif point: # street info can be deduced from the tweet
      return self.next_bus.get_arrival_time(route, point)
    else:
      return "Cannot deduce location info: %s" % text


if __name__ == '__main__':
  try:
    NextRoute().run()
  except KeyboardInterrupt:
    pass
