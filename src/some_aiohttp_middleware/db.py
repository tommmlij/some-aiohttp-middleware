import logging as log
import sys

from aiohttp.web import HTTPInternalServerError, Request, StreamResponse
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from .base import MiddlewareBase

log.getLogger().setLevel("INFO")

default_kwargs = {"db_name": "default"}


class DB(MiddlewareBase):
    @staticmethod
    async def handle(request: Request, *args, **kwargs) -> Request:
        kwargs = default_kwargs | kwargs
        try:
            sm = request.app["db_session_maker"][kwargs["db_name"]]()
        except KeyError:
            raise HTTPInternalServerError(reason="DB session not found")
        if request.get("db_session") is None:
            request["db_session"] = {}
        log.debug(f"Opening session for {kwargs['db_name']}")
        request["db_session"][kwargs["db_name"]] = await sm.__aenter__()
        return request

    @staticmethod
    async def unhandle(
        request: Request, response: StreamResponse, *args, **kwargs
    ) -> StreamResponse:
        kwargs = default_kwargs | kwargs
        session = request["db_session"][kwargs["db_name"]]
        log.debug(f"Closing session for {kwargs['db_name']}")
        await session.__aexit__(*sys.exc_info())
        del request["db_session"][kwargs["db_name"]]
        return response


class CTX:

    def __init__(self, config, name):
        self.config = config
        self.name = name

    def __get__(self, obj, objtype=None):
        config = getattr(obj, self.config)
        name = getattr(obj, self.name)

        async def func(app):

            pool_size_max = getattr(config, "pool_size_max", 20)
            max_overflow = getattr(config, "max_overflow", 10)

            engine = create_async_engine(
                str(config.dsn),
                pool_size=pool_size_max,
                max_overflow=max_overflow,
                pool_pre_ping=True,
            )
            async_session = async_sessionmaker(engine)

            if not app.get("db_session_maker", None):
                app["db_session_maker"] = {}

            app["db_session_maker"].update({name: async_session})

            log.info(
                f"Created postgres pool (max: {pool_size_max}/overflow: {max_overflow}) "
                f"and connected to {config.model_dump()['dsn']}. Available as '{name}'"
            )

            yield

            await engine.dispose()

            log.info("Closed db")

        return func


class Postgres:

    def __init__(self, config, name="default"):
        try:
            getattr(config, "dsn")
        except AttributeError:
            raise RuntimeError("DSN or location of DSN in the configuration needed")
        self.config = config
        self.name = name

    ctx = CTX("config", "name")
