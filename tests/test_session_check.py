import pytest
from aiohttp import web
from aiohttp.web import View
from aiohttp.web_exceptions import HTTPOk
from aiohttp_session import setup, SimpleCookieStorage

from some_aiohttp_middleware import SessionCheck


@pytest.mark.asyncio
async def test_config(caplog, aiohttp_client):
    @SessionCheck.decorate
    class TestView(View):
        async def get(self):
            raise HTTPOk

    app = web.Application()
    setup(app, SimpleCookieStorage())
    app.router.add_view("/", TestView)

    async with await aiohttp_client(app) as client:
        resp = await client.get("/")
        assert resp.status == 500
        assert (
            resp.reason
            == "Missing configuration, either pass 'admin_token' or 'token_location'"
        )


@pytest.mark.asyncio
async def test_middleware(aiohttp_client):
    @AdminAuthHandler.decorate
    class TestView1(View):
        async def get(self):
            raise HTTPOk

    @AdminAuthHandler(admin_token="cb466ec795d74a8eb4a1c49e2feb2acd").decorate
    class TestView2(View):
        async def get(self):
            raise HTTPOk

    app = web.Application()
    setup(app, SimpleCookieStorage())
    app.router.add_view("/tw1", TestView1)
    app.router.add_view("/tw2", TestView2)

    async with await aiohttp_client(app) as client:
        resp = await client.get("/tw1")
        assert resp.status == 422
        resp = await client.get("/tw2")
        assert resp.status == 422
        resp = await client.get("/tw1", headers={"authorization": "bla"})
        assert resp.status == 422
        resp = await client.get("/tw2", headers={"authorization": "bla"})
        assert resp.status == 422
        resp = await client.get("/tw1", headers={"authorization": "Bearer 1"})
        assert resp.status == 401
        resp = await client.get("/tw2", headers={"authorization": "Bearer 1"})
        assert resp.status == 401
        resp = await client.get(
            "/tw1", headers={"authorization": "Bearer cb466ec795d74a8eb4a1c49e2feb2acd"}
        )
        assert resp.status == 200
        resp = await client.get(
            "/tw2", headers={"authorization": "Bearer cb466ec795d74a8eb4a1c49e2feb2acd"}
        )
        assert resp.status == 200
