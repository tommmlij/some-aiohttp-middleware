from aiohttp import web
import inspect

import pytest
from aiohttp.web import View
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
        assert request["amw"] == {'foo': 'bar', 'hello': 'world'}


@pytest.mark.asyncio
async def test_middleware(capfd, aiohttp_client, loop):
    class TestView(View):
        async def get(self):
            assert "amw" in self.request
            assert self.request["amw"] == {'foo': 'bar', 'hello': 'world'}
            print(inspect.currentframe().f_code.co_name, end="_")
            return HTTPOk(text="Hello, world")

    app = web.Application(
        middlewares=[Middleware(foo="bar", hello="world").middleware()]
    )
    app.router.add_view('/', TestView)
    client = await aiohttp_client(app)
    resp = await client.get('/')
    assert resp.status == 200
    text = await resp.text()
    assert 'Hello, world' in text
