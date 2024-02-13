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
        assert "amw" in request
        assert request["amw"] == {'foo': None, 'hello': None}


@pytest.mark.asyncio
async def test_method_no_pars_no_pars(capfd):
    class Test(View):
        @Middleware.decorate
        async def get(self):
            _ = self
            print(inspect.currentframe().f_code.co_name, end="_")
            return HTTPOk()

        @Middleware.decorate
        async def post(self):
            print(inspect.currentframe().f_code.co_name, end="_")
            return HTTPOk()

        async def a(self):
            _ = self
            print(inspect.currentframe().f_code.co_name, end="_")

    await Test(make_mocked_request('GET', '/', headers={'token': 'x11'})).get()
    await Test(make_mocked_request('POST', '/', headers={'token': 'x12'})).post()
    await Test(make_mocked_request('GET', '/', headers={'token': 'x13'})).a()

    out, err = capfd.readouterr()

    assert out == "handle_get_unhandlehandle_post_unhandlea_"


@pytest.mark.asyncio
async def test_method_pars_no_pars(capfd):
    class Test(View):
        @Middleware().decorate
        async def get(self):
            print(inspect.currentframe().f_code.co_name, end="_")
            return HTTPOk()

        @Middleware().decorate
        async def post(self):
            print(inspect.currentframe().f_code.co_name, end="_")
            return HTTPOk()

        async def a(self):
            _ = self
            print(inspect.currentframe().f_code.co_name, end="_")

    await Test(make_mocked_request('GET', '/', headers={'token': 'x14'})).get()
    await Test(make_mocked_request('POST', '/', headers={'token': 'x15'})).post()
    await Test(make_mocked_request('GET', '/', headers={'token': 'x16'})).a()

    out, err = capfd.readouterr()

    assert out == "handle_get_unhandlehandle_post_unhandlea_"


@pytest.mark.asyncio
async def test_method_pars_pars(capfd):
    class Test(View):

        @Middleware().decorate()
        async def get(self):
            _ = self
            print(inspect.currentframe().f_code.co_name, end="_")
            return HTTPOk()

        @Middleware().decorate()
        async def post(self):
            _ = self
            print(inspect.currentframe().f_code.co_name, end="_")
            return HTTPOk()

        async def a(self):
            _ = self
            print(inspect.currentframe().f_code.co_name, end="_")

    await Test(make_mocked_request('GET', '/', headers={'token': 'x17'})).get()
    await Test(make_mocked_request('POST', '/', headers={'token': 'x18'})).post()
    await Test(make_mocked_request('GET', '/', headers={'token': 'x19'})).a()

    out, err = capfd.readouterr()

    assert out == "handle_get_unhandlehandle_post_unhandlea_"


@pytest.mark.asyncio
async def test_method_no_pars_pars(capfd):
    class Test(View):

        @Middleware.decorate()
        async def get(self):
            _ = self
            print(inspect.currentframe().f_code.co_name, end="_")
            return HTTPOk()

        @Middleware.decorate()
        async def post(self):
            _ = self
            print(inspect.currentframe().f_code.co_name, end="_")
            return HTTPOk()

        async def a(self):
            _ = self
            print(inspect.currentframe().f_code.co_name, end="_")

    await Test(make_mocked_request('GET', '/', headers={'token': 'x20'})).get()
    await Test(make_mocked_request('POST', '/', headers={'token': 'x21'})).post()
    await Test(make_mocked_request('GET', '/', headers={'token': 'x22'})).a()

    out, err = capfd.readouterr()

    assert out == "handle_get_unhandlehandle_post_unhandlea_"
