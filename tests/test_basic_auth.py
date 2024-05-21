import pytest
from aiohttp import BasicAuth
from aiohttp.web import Application, Response
from aiohttp.web_exceptions import HTTPOk, HTTPUnauthorized
from aiohttp_pydantic import PydanticView
from pydantic_settings import BaseSettings

from some_aiohttp_middleware.basic_auth import BasicAuth as BasicAuthMiddleware


class MyAfterValidator:
    pass


@pytest.fixture
async def aiohttp_app():
    class Config(BaseSettings):
        users: dict = {"USER_1": "PASSWORD_1", "USER_2": "PASSWORD_2"}

    @BasicAuthMiddleware.decorate
    class View(PydanticView):
        async def get(self):
            return Response(text="ok")

    app = Application()
    app.config = Config()
    app.router.add_view("/test", View)
    return app


@pytest.mark.asyncio
async def test_successful_auth_1(aiohttp_server, aiohttp_client, aiohttp_app, caplog):
    server = await aiohttp_server(aiohttp_app)
    client = await aiohttp_client(server)

    auth = BasicAuth(login="USER_1", password="PASSWORD_1")
    headers = {"Authorization": auth.encode()}

    resp = await client.get("/test", headers=headers)
    assert resp.status == HTTPOk.status_code
    text = await resp.text()
    assert text == "ok"


@pytest.mark.asyncio
async def test_successful_auth_2(aiohttp_server, aiohttp_client, aiohttp_app, caplog):
    server = await aiohttp_server(aiohttp_app)
    client = await aiohttp_client(server)

    auth = BasicAuth(login="USER_2", password="PASSWORD_2")
    headers = {"Authorization": auth.encode()}

    resp = await client.get("/test", headers=headers)
    assert resp.status == HTTPOk.status_code
    text = await resp.text()
    assert text == "ok"


@pytest.mark.asyncio
async def test_unsuccessful_auth(aiohttp_server, aiohttp_client, aiohttp_app, caplog):
    server = await aiohttp_server(aiohttp_app)
    client = await aiohttp_client(server)

    auth = BasicAuth(login="USER_1", password="WRONG_PASSWORD_1")
    headers = {"Authorization": auth.encode()}

    resp = await client.get("/test", headers=headers)
    assert resp.status == HTTPUnauthorized.status_code
    text = await resp.text()
    assert text == "401: Unauthorized"
