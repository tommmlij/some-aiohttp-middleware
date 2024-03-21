import pytest
from aiohttp import web
from aiohttp.web import View
from aiohttp.web_exceptions import HTTPOk

from some_aiohttp_middleware import AdminAuthHandler


@pytest.mark.asyncio
async def test_config(caplog, aiohttp_client):
    @AdminAuthHandler(token_location=["secrets", "admin_token"]).decorate
    class TestView(View):
        async def get(self):
            raise HTTPOk

    app = web.Application()
    app.router.add_view('/', TestView)

    async with await aiohttp_client(app) as client:
        resp = await client.get('/')
        assert resp.status == 500
        assert resp.reason == "Missing configuration"


@pytest.mark.asyncio
async def test_middleware(aiohttp_client):
    @AdminAuthHandler(token_location=["secrets", "admin_token"]).decorate
    class TestView1(View):
        async def get(self):
            raise HTTPOk

    class TestView2(View):
        @AdminAuthHandler(admin_token="cb466ec795d74a8eb4a1c49e2feb2acd").decorate
        async def get(self):
            raise HTTPOk

    app = web.Application()
    app["secrets"] = {
        "admin_token": "cb466ec795d74a8eb4a1c49e2feb2acd"
    }
    app.router.add_view('/tw1', TestView1)
    app.router.add_view('/tw2', TestView2)

    async with await aiohttp_client(app) as client:
        resp = await client.get('/tw1')
        assert resp.status == 422
        resp = await client.get('/tw2')
        assert resp.status == 422
        resp = await client.get('/tw1', headers={"authorization": "bla"})
        assert resp.status == 422
        resp = await client.get('/tw2', headers={"authorization": "bla"})
        assert resp.status == 422
        resp = await client.get('/tw1', headers={"authorization": "Bearer 1"})
        assert resp.status == 401
        resp = await client.get('/tw2', headers={"authorization": "Bearer 1"})
        assert resp.status == 401
        resp = await client.get('/tw1', headers={"authorization": "Bearer cb466ec795d74a8eb4a1c49e2feb2acd"})
        assert resp.status == 200
        resp = await client.get('/tw2', headers={"authorization": "Bearer cb466ec795d74a8eb4a1c49e2feb2acd"})
        assert resp.status == 200
