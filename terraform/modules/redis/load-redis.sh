#!/usr/bin/env bash

team_numbers=$(jq -r 'to_entries | .[] | .key' modules/redis/data/challengers.json)
for team_number in $team_numbers
do
    team_name=$(jq -r ".\"${team_number}\".name" modules/redis/data/challengers.json)
    team_sponsor=$(jq -r ".\"${team_number}\".sponsor" modules/redis/data/challengers.json)
    echo "Loading '$team_number: $team_name / $team_sponsor'"
    echo "MSET dev/$team_number/name \"$team_name\" dev/$team_number/sponsor \"$team_sponsor\" dev/$team_number/png \"$(base64 -i modules/redis/data/$team_number.png | xargs)\"" | \
    redis-cli --tls \
        --cacert ./ssl/CA.pem \
        --cert ./ssl/RedisServer.pem \
        --key ./ssl/RedisServer.key \
        -h app.redis.pro \
        -p 6379
done
