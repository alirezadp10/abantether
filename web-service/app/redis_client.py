import os
import redis

class RedisClient:
    def __init__(self):
        redis_host = os.getenv('REDIS_HOST', 'redis')
        redis_port = os.getenv('REDIS_PORT', 6379)
        self.client = redis.StrictRedis(host=redis_host, port=redis_port, db=0)