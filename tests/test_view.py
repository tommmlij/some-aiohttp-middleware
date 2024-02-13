import inspect

import pytest
from aiohttp.web import View
from aiohttp.test_utils import make_mocked_request
from aiohttp.web_exceptions import HTTPOk

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


@pytest.mark.asyncio
async def test_class_kwargs_method_kwargs(capfd):
    @Middleware(hello="world").decorate(foo="bar")
    class Test(View):
        @staticmethod
        async def get():
            print(inspect.currentframe().f_code.co_name, end="_")
            return HTTPOk()

        async def post(self):
            _ = self
            print(inspect.currentframe().f_code.co_name, end="_")
            return HTTPOk()

        async def a(self):
            _ = self
            print(inspect.currentframe().f_code.co_name, end="_")

    await Test(make_mocked_request('GET', '/', headers={'token': 'x'})).get()
    await Test(make_mocked_request('POST', '/', headers={'token': 'x'})).post()
    await Test(make_mocked_request('GET', '/', headers={'token': 'x'})).a()

    out, err = capfd.readouterr()

    assert out == "bar_world_handle_get_bar_world_unhandlebar_world_handle_post_bar_world_unhandlea_"
