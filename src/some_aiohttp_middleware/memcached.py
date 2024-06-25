import logging as log
import sys

from aiohttp.web import HTTPInternalServerError, Request, StreamResponse
from pydantic import IPvAnyAddress, conint
from pydantic_settings import BaseSettings
from aiomcache import Client

from .base import MiddlewareBase

log.getLogger().setLevel("INFO")


class MemcachedConfig(BaseSettings):
    host: IPvAnyAddress | str = "localhost"
    port: conint(ge=1024, le=65535) = 11211

    class Config:
        env_prefix = "S_"


class Memcached(MiddlewareBase):
    @staticmethod
    async def handle(request: Request, *args, **kwargs) -> Request:
        config = getattr(request.app, "config")

        if not config:
            raise RuntimeError("No app configuration found")

        try:
            memcached_config = getattr(config, "memcached")
        except AttributeError:
            raise RuntimeError("Memcached definition needed in the configuration")

        request["memcached"] = Client(getattr(memcached_config, "host"), getattr(memcached_config, "port"))

        return request

    @staticmethod
    async def unhandle(
            request: Request, response: StreamResponse, *args, **kwargs
    ) -> StreamResponse:

        client = request.get("memcached")
        if client:
            await client.close()

        return response
