# 说明

使用 Docker Compose 本地部署基于 Sentinel 的高可用 Redis 集群。

项目地址：[https://github.com/TomCzHen/redis-sentinel-sample](https://github.com/TomCzHen/redis-sentinel-sample)

根据官方文档 [Redis Sentinel Documentation](https://redis.io/topics/sentinel) 中的 [Example 2: basic setup with three boxes](https://redis.io/topics/sentinel#example-2-basic-setup-with-three-boxes) 示例创建的实例，但因为是单机部署，所以不满足 Redis 实例与 Sentinel 实例分别处于 3 台机器的要求，因此仅用于开发环境测试与学习。

## 使用方法

使用 `docker-compose up -d` 部署运行。

使用 `docker-compose pause master` 可以模拟对应的 Redis 实例不可用。

使用 `docker-compose pause sentinel-1` 可以模拟对应的 Sentinel 实例不可用。

使用 `docker-compose unpause service_name` 将暂停的容器恢复运行。

使用支持 Sentinel 的客户端连接 `localhost:62379` 进行应用测试。

注：Windows 和 Mac 可能需要修改 `Volumes` 挂载参数。

## 注意事项

[Sentinel, Docker, NAT, and possible issues](https://redis.io/topics/sentinel#sentinel-docker-nat-and-possible-issues)

将容器端口 `EXPOSE` 时，Sentinel 所发现的 master/slave 连接信息（IP 和 端口）对客户端来说不一定可用。

例如：将 Reids 实例端口 `6379` `EXPOSE` 为 `16379`, Sentinel 容器使用 `LINK` 的方式访问 Redis 容器，那么对于 Sentinel 容器 `6379` 端口是可用的，但对于外部客户端是不可用的。

解决方法是 `EXPOSE` 端口时保持内外端口一致，或者使用 `host` 网络运行容器。如果你想使用本项目中的编排文件部署的集群对外部可用，那么只能将 Redis 容器运行在 `host` 网络之上。

注：实际上 `bridge` 模式下 Redis 性能也会受到影响。

## 文件结构
```
.
├── docker-compose.yaml
├── nginx
│   └── nginx.conf
├── README.md
├── .env
└── sentinel
    ├── docker-entrypoint.sh
    ├── Dockerfile-sentinel
    └── sentinel.conf.sample
```

### Sentinel

镜像使用 `Dockerfile-sentinel` 构建，运行时根据环境变量生成 `sentinel.conf` 文件，详细配置说明请查看 `sentinel.conf.sample` 内容。

#### docker-entrypoint.sh

使用 Reids 官方镜像中的 `docker-entrypoint.sh` 脚本修改而来，添加了生成 `sentienl.conf` 语句。

```shell
...
# create sentinel.conf
if [ ! -e ${SENTINEL_CONF_PATH} ]; then
    envsubst < /etc/redis/sentinel.conf.sample > ${SENTINEL_CONF_PATH}
    chown redis:redis /etc/redis/sentinel.conf
fi
...
```

修改配置 Sentinel 的环境变量后需要重新创建容器才能生效。

#### 可用环境变量

```shell
SENTINEL_CONF_PATH=/etc/redis/sentinel.conf
SENTINEL_PORT=26379
SENTINEL_MASTER_NAME=redis-master
SENTINEL_REDIS_IP=127.0.0.1
SENTINEL_REDIS_PORT=6379
SENTINEL_REDIS_PWD=
SENTINEL_QUORUM=2
SENTINEL_DOWN_AFTER=30000
SENTINEL_PARALLEL_SYNCS=1
SENTINEL_FAILOVER_TIMEOUT=180000
```
### docker-compose.yaml

可以使用 `docker-compose config` 可查看完整的编排内容。

#### Redis 实例运行参数

详细可用参数请查看官方示例文件 [Redis Configuration File Example](https://raw.githubusercontent.com/antirez/redis/4.0/redis.conf)，需要注意 `port` 参数需要与编排中的 `PORTS` 保持一致，或修改编排文件让容器网络使用 `host` 模式。

由于 master 会被 Sentinel 切换为 slave ，因此最好保持每个 Redis 实例的口令一致。

```
master:
    image: redis:4.0.8-alpine
    ports:
      - 6379:6379
    volumes:
      - type: volume
        source: master-data
        target: /data
    command: [
      '--requirepass "${REDIS_PWD}"',
      '--masterauth "${REDIS_PWD}"',
      '--maxmemory 512mb',
      '--maxmemory-policy volatile-ttl',
      '--save ""',
    ]
```

#### Sentinel 实例运行参数

详细可用参数请查看 sentinel 目录下的 `sentinel.conf.sample` 文件。由于容器使用的配置文件是运行时根据环境变量生成的，因此使用 `environment` 进行配置，可用环境变量请查看文档 Sentinel 部分。

最后使用了 Nginx 作为 Sentinel 实例的代理，因此 Sentinel 容器不需要对外访问。

```
sentinel-1: &sentinel
    build:
      context: ./sentinel
      dockerfile: Dockerfile-sentinel
    image: redis-sentinel:dev
    environment:
      - SENTINEL_REDIS_PWD=${REDIS_PWD}
      - SENTINEL_REDIS_IP=${SENTINEL_MASTER_NAME}
      - SENTINEL_QUORUM=2
      - SENTINEL_DOWN_AFTER=3000
    command: [
      '${SENTINEL_CONF_PATH}',
      '--sentinel'
    ]
    depends_on:
      - master
      - node-1
      - node-2
    links:
      - master:${SENTINEL_MASTER_NAME}
      - node-1
      - node-2
  sentinel-2:
    <<: *sentinel
  sentinel-3:
    <<: *sentinel
```

#### Nginx 

使用 Nginx 作为 Sentinel 负载均衡以及高可用代理。

```
  nginx:
    image: nginx:1.13.9-alpine
    ports:
      - 26379:26379
    volumes:
      - type: bind
        source: ./nginx/nginx.conf
        target: /etc/nginx/nginx.conf
        read_only: true
    depends_on:
      - sentinel-1
      - sentinel-2
      - sentinel-3
```

修改 nginx 目录下的 `nginx.conf` 进行配置。

```
...
stream {
    server {
        listen 26379;
        proxy_pass redis_sentinel;
    }

    upstream redis_sentinel {
        server sentinel-1:26379;
        server sentinel-2:26379;
        server sentinel-3:26379;
    }
}
...

```