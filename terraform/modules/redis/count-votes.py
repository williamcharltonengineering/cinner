#!.venv/bin/python

import os
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
r = redis.Redis(**tls_config)

# A dictionary to hold the counts
team_counts = {}

# Using SCAN to retrieve keys
total_votes = 0
cursor = '0'
while cursor != 0:
    cursor, keys = r.scan(cursor=cursor, match='dev/*/votes/*')
    for key in keys:
        # Extract team name from the key
        parts = key.decode().split('/')
        print(f'parts: {parts}')
        team_name = parts[1]
        
        # Increment the count for this team
        team_counts[team_name] = team_counts.get(team_name, 0) + 1
        total_votes += 1

# Sort teams by count
sorted_teams = sorted(team_counts.items(), key=lambda x: x[1], reverse=True)

# Print or process the sorted list
for team, count in sorted_teams:
    print(f"Team: {team}, Votes: {count}")
print(f'Total votes: {total_votes}')