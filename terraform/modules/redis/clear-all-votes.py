#!.venv/bin/python

import os
import sys
import redis

here_dir = os.path.abspath(os.path.dirname(__file__))

tls_config = {
    'host': 'leecountychilichallenge2024.com',
    'port': 6379,
    'db': 0,
    'ssl': True,
    'ssl_ca_certs': os.path.join(here_dir, '..', '..', 'ssl', 'CA.pem'),
    'ssl_certfile': os.path.join(here_dir, '..', '..', 'ssl', 'RedisClient.pem'),
    'ssl_keyfile':  os.path.join(here_dir, '..', '..', 'ssl', 'RedisClient.key'),
}
print(tls_config)
r = redis.Redis(**tls_config)

# A dictionary to hold the counts
team_counts = {}

# Using SCAN to retrieve keys
cursor = '0'
while cursor != 0:
    cursor, keys = r.scan(cursor=cursor, match='dev/*/votes/*')
    for key in keys:
        print(f'deleting key: {key}')
        if len(sys.argv) > 1:
            if sys.argv[1] == '--hot':
                if 'y' == input('\n\tare you sure? '):
                    r.delete(key)

print("All matching keys have been deleted.")
