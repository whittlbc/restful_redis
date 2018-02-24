import json
import os
from definitions import *
from redis import StrictRedis
from exps import *


class RestfulRedisServer(object):

  def __init__(self, target, url=None, channel=default_channel):
    url = url or os.environ.get('REDIS_URL') or default_url
    self.redis = StrictRedis.from_url(url=url)
    self.channel = channel
    self.target = target

  def run(self):
    while True:
      # Block infinitely until request received
      request = self.redis.blpop(self.channel)

      try:
        # Attempt to parse JSON request data
        payload = json.loads(request[1]) or {}
      except:
        raise JsonParseException(request)

      # Get request uid and ensure its presence
      request_uid = payload.get('request_uid')

      if not request_uid:
        raise InvalidRequestException(payload)

      resp = {'ok': True}

      try:
        # Call target function
        resp['data'] = self.target(payload.get('data', {}))
      except BaseException as e:
        resp['ok'] = False
        resp['data'] = e.message

      # Push the JSON response to channel=request_uid
      self.redis.rpush(request_uid, json.dumps(resp))