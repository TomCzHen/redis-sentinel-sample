#!/usr/bin/python3
# -*- coding: utf-8 -*-

from redis.sentinel import Sentinel
from time import sleep


def discover_master(s: Sentinel):
    master = None
    try:
        master = s.discover_master(redis_master_name)
    except Exception as Err:
        pass

    return master or "No master found."


def discover_slave(s: Sentinel):
    slave = None
    try:
        slave = s.discover_slaves(redis_master_name)
    except Exception as Err:
        pass

    return slave or "No slave found."


def get_redis_master_run_id(s: Sentinel, master_name: str) -> str:
    master = None
    try:
        master = s.master_for(redis_master_name).info(section="Server").get("run_id")
    except Exception as Err:
        pass

    return master or "Can't get master run id."


if __name__ == '__main__':
    redis_master_name = "redis-master"
    redis_pwd = "P@ssw0rd"
    while True:
        sentinel = Sentinel([('localhost', 26379)], socket_timeout=0.1, password=redis_pwd)
        print("Redis Master Run ID : {}".format(get_redis_master_run_id(sentinel, redis_master_name)))
        print("Redis Master : {}".format(discover_master(sentinel)))
        print("Redis Slave : {}".format(discover_slave(sentinel)))
        sleep(5)