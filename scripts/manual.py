import asyncio
import inspect

from aiohttp.test_utils import make_mocked_request
from aiohttp.web import View, HTTPOk

from advanced_middleware import MiddlewareBase


class Middleware(MiddlewareBase):

    @staticmethod
    async def handle(*args, **kwargs):
        if kwargs.get("foo"):
            print(kwargs.get("foo"), end="_")
        if kwargs.get("hello"):
            print(kwargs.get("hello"), end="_")
        print("handle", end="_")

    @staticmethod
    async def unhandle(*args, **kwargs):
        if kwargs.get("foo"):
            print(kwargs.get("foo"), end="_")
        if kwargs.get("hello"):
            print(kwargs.get("hello"), end="_")
        print("unhandle", end="")


async def main():
    @Middleware(hello="world").decorate(foo="bar")
    class Test(View):
        @staticmethod
        async def get():
            print(inspect.currentframe().f_code.co_name, end="_")
            return HTTPOk()

        async def post(self):
            _ = self
            print(inspect.currentframe().f_code.co_name, end="_")
            print()
            print(self.request)
            print(self.request.headers)
            print()
            return HTTPOk()

        async def a(self):
            _ = self
            print(inspect.currentframe().f_code.co_name, end="_")
            return HTTPOk()

    resp2 = await Test(make_mocked_request('POST', '/', headers={'token': 'x'})).post()
    print()

    print(resp2)
    print(type(resp2))


if __name__ == '__main__':
    asyncio.run(main())
