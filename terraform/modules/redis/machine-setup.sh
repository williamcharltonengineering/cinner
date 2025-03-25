#!/bin/sh

set -x

curl -fsSL https://packages.redis.io/gpg | sudo gpg --yes --dearmor -o /usr/share/keyrings/redis-archive-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/redis-archive-keyring.gpg] https://packages.redis.io/deb $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/redis.list

apt update
DEBIAN_FRONTEND=noninteractive \
    apt upgrade -y \
        openssh-client \
        lsb-release \
        curl \
        gpg \
        redis

rm -rf /var/cache/apk/*

REDIS_SECURE_PASSWORD="${1}"

groupadd -g 1001 redis
useradd -m -u 1001 -g redis redis
usermod -aG sudo redis
usermod -p $(echo -n "${REDIS_SECURE_PASSWORD}" | openssl passwd -1 -stdin) redis # create encrypted password
passwd -l redis
usermod -m -d /home/redis redis
# NOTE
# The following block up until the ssh bit is to address 
# the following warnings in the redis-server.log
#    5675:M 05 Jan 2024 22:03:42.302 # WARNING overcommit_memory is set to 0! Background save may fail under low memory condition. To fix this issue add 'vm.overcommit_memory = 1' to /etc/sysctl.conf and then reboot or run the command 'sysctl vm.overcommit_memory=1' for this to take effect.
#    5675:M 05 Jan 2024 22:03:42.302 # WARNING you have Transparent Huge Pages (THP) support enabled in your kernel. This will create latency and memory usage issues with Redis. To fix this issue run the command 'echo madvise > /sys/kernel/mm/transparent_hugepage/enabled' as root, and add it to your /etc/rc.local in order to retain the setting after a reboot. Redis must be restarted after THP is disabled (set to 'madvise' or 'never').
cat <<EOF > /etc/systemd/system/disable-thp.service
[Unit]
Description=Disable Transparent Huge Pages (THP)

[Service]
Type=oneshot
ExecStart=/bin/sh -c "echo madvise > /sys/kernel/mm/transparent_hugepage/enabled"

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable disable-thp.service
systemctl start disable-thp.service

echo madvise > /sys/kernel/mm/transparent_hugepage/enabled
echo 'vm.overcommit_memory = 1' >> /etc/sysctl.conf
# END NOTE

# mkdir -p ~redis/.ssh
# echo \"${REDIS_SSH_PUBKEY}\" | tr -d '"' | xargs > ~redis/.ssh/authorized_keys
# chmod 700 ~redis/.ssh
# chmod 600 ~redis/.ssh/authorized_keys
# chown -R redis:redis ~redis/.ssh
# echo 'Match User redis' >> /etc/ssh/sshd_config
# echo '    PasswordAuthentication no' >> /etc/ssh/sshd_config
# nohup bash -c 'sleep 5 && sudo service ssh restart' &
