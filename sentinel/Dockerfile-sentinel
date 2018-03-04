FROM redis:4.0.8-alpine

ENV SENTINEL_CONF_PATH=/etc/redis/sentinel.conf \
    SENTINEL_PORT=26379 \
    SENTINEL_MASTER_NAME=redis-master \
    SENTINEL_REDIS_IP=127.0.0.1 \
    SENTINEL_REDIS_PORT=6379 \
    SENTINEL_REDIS_PWD= \
    SENTINEL_QUORUM=2 \
    SENTINEL_DOWN_AFTER=30000 \
    SENTINEL_PARALLEL_SYNCS=1 \
    SENTINEL_FAILOVER_TIMEOUT=180000

RUN apk add --no-cache gettext

ADD sentinel.conf.sample /etc/redis/sentinel.conf.sample

COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh
ENTRYPOINT ["docker-entrypoint.sh"]

EXPOSE 26379
CMD ["redis-server"]
