import pytest
from aiohttp import web
from aiohttp.web import View
from aiohttp.web_exceptions import HTTPOk
from aiohttp.web_response import Response

from some_aiohttp_middleware import MiddlewareBase


class Middleware1(MiddlewareBase):

    @staticmethod
    async def handle(request, *args, **kwargs):
        if "awm" not in request:
            request["awm"] = {}
        request["awm"].update(
            {"foo": kwargs.get("foo", None), "hello": kwargs.get("hello", None)}
        )

    @staticmethod
    async def unhandle(request, response, *args, **kwargs):
        assert "awm" in request
        assert request["awm"]["foo"] == "bar"
        assert request["awm"]["hello"] == "world"


class Middleware2(MiddlewareBase):

    @staticmethod
    async def handle(request, *args, **kwargs):
        if "awm" not in request:
            request["awm"] = {}
        request["awm"].update({"hey": kwargs.get("hey", None)})

    @staticmethod
    async def unhandle(request, response, *args, **kwargs):
        assert "awm" in request
        assert request["awm"]["hey"] == "you"


@pytest.mark.asyncio
async def test_middleware(aiohttp_client):
    class TestView1(View):
        async def get(self):
            assert "awm" in self.request
            assert self.request["awm"] == {"foo": "bar", "hello": "world", "hey": "you"}
            raise HTTPOk(text="Hello, world")

    # We test also with a response object for coverage of routes where no HTTPException was raised
    class TestView2(View):
        async def get(self):
            assert "awm" in self.request
            assert self.request["awm"] == {"foo": "bar", "hello": "world", "hey": "you"}
            return Response(text="Hello, world")

    app = web.Application(
        middlewares=[
            Middleware1(foo="bar", hello="world").middleware(),
            Middleware2(hey="you").middleware(),
        ]
    )
    app.router.add_view("/tw1", TestView1)
    app.router.add_view("/tw2", TestView2)
    async with await aiohttp_client(app) as client:
        resp = await client.get("/tw1")
        assert resp.status == 200
        text = await resp.text()
        assert "Hello, world" in text
        resp = await client.get("/tw2")
        assert resp.status == 200
        text = await resp.text()
        assert "Hello, world" in text
