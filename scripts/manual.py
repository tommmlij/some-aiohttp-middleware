import asyncio
import inspect

from aiohttp.test_utils import make_mocked_request
from aiohttp.web import View, HTTPOk

from advanced_middleware import MiddlewareBase


class Middleware(MiddlewareBase):

    @staticmethod
    async def handle(request, **kwargs):
        print("handle")
        request["amw"] = {
            "foo": kwargs.get("foo", None),
            "hello": kwargs.get("hello", None)
        }

    @staticmethod
    async def unhandle(request, response, **kwargs):
        print("unhandle")
        assert "amw" in request
        assert request["amw"] == {'foo': 'bar', 'hello': 'world'}

        return response


async def main():
    class Test(View):
        @staticmethod
        async def get():
            return HTTPOk()

        @Middleware(hello="world").decorate(foo="bar")
        async def post(self):
            assert "amw" in self.request
            assert self.request["amw"] == {'foo': 'bar', 'hello': 'world'}
            return HTTPOk()

        async def a(self):
            _ = self
            print(inspect.currentframe().f_code.co_name, end="_")
            return HTTPOk()

    resp1 = await Test(make_mocked_request('GET', '/', headers={'token': 'x'})).get()
    resp2 = await Test(make_mocked_request('POST', '/', headers={'token': 'x'})).post()


if __name__ == '__main__':
    asyncio.run(main())
