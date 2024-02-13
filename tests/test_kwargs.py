import inspect

import pytest
from aiohttp.web import View
from aiohttp.test_utils import make_mocked_request
from aiohttp.web_exceptions import HTTPOk

from advanced_middleware import MiddlewareBase


class Middleware(MiddlewareBase):

    @staticmethod
    async def handle(request, *args, **kwargs):
        print("handle", end="_")
        request["amw"] = {
            "foo": kwargs.get("foo", None),
            "hello": kwargs.get("hello", None)
        }

    @staticmethod
    async def unhandle(request, response, *args, **kwargs):
        print("unhandle", end="")


@pytest.mark.asyncio
async def test_method_kwargs_method_kwargs(capfd):
    class Test(View):
        @Middleware(hello="world").decorate(foo="bar")
        async def get(self):
            assert "amw" in self.request
            assert self.request["amw"] == {'foo': 'bar', 'hello': 'world'}
            print(inspect.currentframe().f_code.co_name, end="_")
            return HTTPOk()

        @Middleware(hello="world").decorate(foo="bar")
        async def post(self):
            assert "amw" in self.request
            assert self.request["amw"] == {'foo': 'bar', 'hello': 'world'}
            print(inspect.currentframe().f_code.co_name, end="_")
            return HTTPOk()

        async def a(self):
            _ = self
            print(inspect.currentframe().f_code.co_name, end="_")

    await Test(make_mocked_request('GET', '/', headers={'token': 'x1'})).get()
    await Test(make_mocked_request('POST', '/', headers={'token': 'x2'})).post()
    await Test(make_mocked_request('GET', '/', headers={'token': 'x3'})).a()

    out, err = capfd.readouterr()

    assert out == "handle_get_unhandlehandle_post_unhandlea_"


@pytest.mark.asyncio
async def test_method_kwargs_method(capfd):
    class Test(View):
        @Middleware(hello="world").decorate
        async def get(self):
            assert "amw" in self.request
            assert self.request["amw"] == {'foo': None, 'hello': 'world'}
            print(inspect.currentframe().f_code.co_name, end="_")
            return HTTPOk()

        @Middleware(hello="world").decorate
        async def post(self):
            assert "amw" in self.request
            assert self.request["amw"] == {'foo': None, 'hello': 'world'}

            print(inspect.currentframe().f_code.co_name, end="_")
            return HTTPOk()

        async def a(self):
            _ = self
            print(inspect.currentframe().f_code.co_name, end="_")

    await Test(make_mocked_request('GET', '/', headers={'token': 'x4'})).get()
    await Test(make_mocked_request('POST', '/', headers={'token': 'x5'})).post()
    await Test(make_mocked_request('GET', '/', headers={'token': 'x6'})).a()

    out, err = capfd.readouterr()

    assert out == "handle_get_unhandlehandle_post_unhandlea_"


@pytest.mark.asyncio
async def test_method_method_kwargs(capfd):
    class Test(View):
        @Middleware.decorate(foo="bar")
        async def get(self):
            assert "amw" in self.request
            assert self.request["amw"] == {'foo': 'bar', 'hello': None}
            print(inspect.currentframe().f_code.co_name, end="_")
            return HTTPOk()

        @Middleware.decorate(foo="bar")
        async def post(self):
            assert "amw" in self.request
            assert self.request["amw"] == {'foo': 'bar', 'hello': None}
            print(inspect.currentframe().f_code.co_name, end="_")
            return HTTPOk()

        async def a(self):
            _ = self
            print(inspect.currentframe().f_code.co_name, end="_")

    await Test(make_mocked_request('GET', '/', headers={'token': 'x7'})).get()
    await Test(make_mocked_request('POST', '/', headers={'token': 'x8'})).post()
    await Test(make_mocked_request('GET', '/', headers={'token': 'x9'})).a()

    out, err = capfd.readouterr()

    assert out == "handle_get_unhandlehandle_post_unhandlea_"
