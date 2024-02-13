import asyncio

from aiohttp import web
import inspect

from aiohttp.web import View, run_app
from aiohttp.web_exceptions import HTTPOk
from aiohttp.web_middlewares import middleware
from aiohttp.web_response import json_response

from advanced_middleware import MiddlewareBase
from advanced_middleware.admin_auth_handler import AdminAuthHandler


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


@AdminAuthHandler.decorate
class TestView(View):
    async def get(self):
        assert "amw" in self.request
        assert self.request["amw"] == {'foo': 'bar', 'hello': 'world'}
        print(inspect.currentframe().f_code.co_name, end="_")
        return HTTPOk(text="Hello, world")


if __name__ == '__main__':
    app = web.Application(
        middlewares=[
        ]
    )
    app.router.add_view('/', TestView)

    run_app(app, port=1500)
