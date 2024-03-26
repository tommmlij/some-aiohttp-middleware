import inspect

import pytest
from aiohttp.test_utils import make_mocked_request
from aiohttp.web import View
from aiohttp.web_exceptions import HTTPOk

from some_aiohttp_middleware import MiddlewareBase


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
async def test_class_no_pars_no_pars(capfd):
    @Middleware.decorate
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

    await Test(make_mocked_request("GET", "/", headers={"token": "x21"})).get()
    await Test(make_mocked_request("POST", "/", headers={"token": "x22"})).post()
    await Test(make_mocked_request("GET", "/", headers={"token": "x23"})).a()

    out, err = capfd.readouterr()

    assert out == "handle_get_unhandlehandle_post_unhandlea_"


@pytest.mark.asyncio
async def test_class_pars_no_pars(capfd):
    @Middleware().decorate
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

    await Test(make_mocked_request("GET", "/", headers={"token": "x24"})).get()
    await Test(make_mocked_request("POST", "/", headers={"token": "x25"})).post()
    await Test(make_mocked_request("GET", "/", headers={"token": "x26"})).a()

    out, err = capfd.readouterr()

    assert out == "handle_get_unhandlehandle_post_unhandlea_"


@pytest.mark.asyncio
async def test_class_pars_pars(capfd):
    @Middleware().decorate()
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

    await Test(make_mocked_request("GET", "/", headers={"token": "x27"})).get()
    await Test(make_mocked_request("POST", "/", headers={"token": "x28"})).post()
    await Test(make_mocked_request("GET", "/", headers={"token": "x29"})).a()

    out, err = capfd.readouterr()

    assert out == "handle_get_unhandlehandle_post_unhandlea_"


@pytest.mark.asyncio
async def test_class_no_pars_pars(capfd):
    @Middleware.decorate()
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

    await Test(make_mocked_request("GET", "/", headers={"token": "x30"})).get()
    await Test(make_mocked_request("POST", "/", headers={"token": "x31"})).post()
    await Test(make_mocked_request("GET", "/", headers={"token": "x32"})).a()

    out, err = capfd.readouterr()

    assert out == "handle_get_unhandlehandle_post_unhandlea_"


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

    await Test(make_mocked_request("GET", "/", headers={"token": "x33"})).get()
    await Test(make_mocked_request("POST", "/", headers={"token": "x34"})).post()
    await Test(make_mocked_request("GET", "/", headers={"token": "x35"})).a()

    out, err = capfd.readouterr()

    assert (
        out
        == "bar_world_handle_get_bar_world_unhandlebar_world_handle_post_bar_world_unhandlea_"
    )


@pytest.mark.asyncio
async def test_class_kwargs_method(capfd):
    @Middleware(hello="world").decorate
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

    await Test(make_mocked_request("GET", "/", headers={"token": "x36"})).get()
    await Test(make_mocked_request("POST", "/", headers={"token": "x37"})).post()
    await Test(make_mocked_request("GET", "/", headers={"token": "x38"})).a()

    out, err = capfd.readouterr()

    assert out == "world_handle_get_world_unhandleworld_handle_post_world_unhandlea_"


@pytest.mark.asyncio
async def test_class_method_kwargs(capfd):
    @Middleware.decorate(foo="bar")
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

    await Test(make_mocked_request("GET", "/", headers={"token": "x39"})).get()
    await Test(make_mocked_request("POST", "/", headers={"token": "x40"})).post()
    await Test(make_mocked_request("GET", "/", headers={"token": "x41"})).a()

    out, err = capfd.readouterr()

    assert out == "bar_handle_get_bar_unhandlebar_handle_post_bar_unhandlea_"
