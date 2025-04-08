import logging as log
import sys
from typing import Literal

from aiohttp.web import HTTPInternalServerError, Request, StreamResponse
from pydantic_settings import BaseSettings
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from .base import MiddlewareBase

from pydantic import (  # isort:skip
    Field,
    IPvAnyAddress,
    PostgresDsn,
    SecretStr,
    computed_field,
    conint,
    field_serializer,
)


log.getLogger().setLevel("INFO")

default_kwargs = {"db_name": "default"}


class DBConfig(BaseSettings):
    scheme: Literal["postgresql+asyncpg"] = "postgresql+asyncpg"
    host: IPvAnyAddress | str = "localhost"
    port: conint(ge=1024, le=65535) = 5432
    username: str = "postgres"
    password: SecretStr = Field(default="postgres", exclude=False)
    database: str = "postgres"
    pool_overflow: conint(ge=1, le=1000) = 10
    pool_size_max: conint(ge=1, le=1000) = 50
    pool_timeout: conint(ge=1, le=1000) = 120

    class Config:
        env_prefix = "S_"

    def create_dsn(self, obfuscated=True):
        pw = self.password if obfuscated else self.password.get_secret_value()
        return PostgresDsn(
            f"{self.scheme}://{self.username}:{pw}@{self.host}:{self.port}/{self.database}"
        )

    @computed_field(repr=True)
    @property
    def dsn(self) -> PostgresDsn:
        return self.create_dsn(obfuscated=False)

    @field_serializer("dsn")
    def obfuscated(self, _dsn: PostgresDsn):
        return self.create_dsn()


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
                config.dsn.get_secret_value() if isinstance(config.dsn, SecretStr) else str(config.dsn),
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
