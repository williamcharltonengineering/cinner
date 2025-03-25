#!/usr/bin/env bash


redis-cli \
    --tls \
    --cacert ./ssl/CA.pem \
    --cert ./ssl/RedisClient.pem \
    --key ./ssl/RedisClient.key \
    -h app.presis.pro \
    -p 6379 \
    ping

exit 0