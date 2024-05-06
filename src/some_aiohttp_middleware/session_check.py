from aiohttp_session import get_session

from .base import MiddlewareBase

from aiohttp.web_exceptions import HTTPUnauthorized


class SessionCheck(MiddlewareBase):

    @staticmethod
    async def handle(request, *args, **kwargs):

        if not await get_session(request):
            raise HTTPUnauthorized

        return request
