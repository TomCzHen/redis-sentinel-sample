#!/bin/sh
set -e

# create sentinel.conf
if [ ! -e ${SENTINEL_CONF_PATH} ]; then
    envsubst < /etc/redis/sentinel.conf.sample > ${SENTINEL_CONF_PATH}
    chown redis:redis /etc/redis/sentinel.conf
fi

# wating for master

until $(redis-cli -h "${SENTINEL_MASTER_NAME}" -p "${SENTINEL_REDIS_PORT}" -a "${SENTINEL_REDIS_PORT}") ; do
  >&2 echo "Redis master is unavailable - sleeping"
  sleep 3
done

# first arg is `-f` or `--some-option`
# or first arg is `something.conf`
if [ "${1#-}" != "$1" ] || [ "${1%.conf}" != "$1" ]; then
	set -- redis-server "$@"
fi

# allow the container to be started with `--user`
if [ "$1" = 'redis-server' -a "$(id -u)" = '0' ]; then
	chown -R redis .
	exec su-exec redis "$0" "$@"
fi

exec "$@"
