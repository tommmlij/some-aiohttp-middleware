import operator
import sys
import re

import logging as log
from functools import reduce

from aiohttp.web import Request, HTTPInternalServerError, StreamResponse
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from .base import MiddlewareBase

log.getLogger().setLevel("INFO")

default_kwargs = {"db_name": "default"}


class DB(MiddlewareBase):
    @staticmethod
    async def handle(request: Request, *args, **kwargs) -> Request:
        kwargs = default_kwargs | kwargs
        try:
            sm = request.app['db_session_maker'][kwargs['db_name']]()
        except KeyError:
            raise HTTPInternalServerError(reason="DB session not found")
        if request.get('db_session') is None:
            request['db_session'] = {}
        log.debug(f"Opening session for {kwargs['db_name']}")
        request['db_session'][kwargs['db_name']] = await sm.__aenter__()
        return request

    @staticmethod
    async def unhandle(request: Request, response: StreamResponse, *args, **kwargs) -> StreamResponse:
        kwargs = default_kwargs | kwargs
        session = request['db_session'][kwargs['db_name']]
        log.debug(f"Closing session for {kwargs['db_name']}")
        await session.__aexit__(*sys.exc_info())
        del request['db_session'][kwargs['db_name']]
        return response


def obfuscate_password(dsn):
    """Helper function to replace the password of a dsn with asterisks

    :param dsn: String of the dsn to obfuscate.
    :return: The obfuscated dsn string.
    """

    reg = r'^(?P<conn>.*?):\/\/' \
          r'(?P<user>.*?):(?P<passwd>.*)@' \
          r'(?P<addr>[^\(]*):(?P<port>[^\)]*)\/' \
          r'(?P<dbname>.*?)$'
    return re.sub(reg, r'\g<conn>://\g<user>:*****@\g<addr>:\g<port>/\g<dbname>', dsn)


class CTX:

    def __init__(self, dsn, dsn_location, name, pool_size_max, pool_overflow):
        self.dsn = dsn
        self.dsn_location = dsn_location
        self.name = name
        self.pool_size_max = pool_size_max
        self.pool_overflow = pool_overflow

    def __get__(self, obj, objtype=None):
        print("__GET__")
        dsn = getattr(obj, self.dsn)
        dsn_location = getattr(obj, self.dsn_location)
        name = getattr(obj, self.name)
        pool_size_max = getattr(obj, self.pool_size_max)
        pool_overflow = getattr(obj, self.pool_overflow)

        async def func(app):

            resolved_dsn = dsn or reduce(operator.getitem, dsn_location, app)

            dsn_log = obfuscate_password(resolved_dsn)

            engine = create_async_engine(resolved_dsn,
                                         pool_size=pool_size_max,
                                         max_overflow=pool_overflow,
                                         pool_pre_ping=True
                                         )
            async_session = async_sessionmaker(engine)

            if not app.get('db_session_maker', None):
                app['db_session_maker'] = {}

            app['db_session_maker'].update({name: async_session})

            log.info(
                f'Created postgres pool (max: {pool_size_max}/overflow: {pool_overflow}) and connected to {dsn_log}. '
                f'Available as "{name}"')

            yield

            await engine.dispose()

            log.info('Closed db')

        return func


class Postgres:

    def __init__(self, dsn=None, dsn_location=None, name="default", pool_size_max=10, pool_overflow=10):

        assert not (dsn is None and dsn_location is None), \
            "DSN or location of DSN in the configuration needed"

        self.dsn = dsn
        self.dsn_location = dsn_location
        self.name = name
        self.pool_size_max = pool_size_max
        self.pool_overflow = pool_overflow

    ctx = CTX("dsn", "dsn_location", "name", "pool_size_max", "pool_overflow")
