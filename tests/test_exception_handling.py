import logging

import pytest
from aiohttp import web
from aiohttp.web import View
from aiohttp.web_exceptions import HTTPInternalServerError

from some_aiohttp_middleware import DB, Postgres


@pytest.mark.asyncio
async def test_middleware(caplog, aiohttp_client):
    @DB(db_name="backend1").decorate
    class TestView1(View):
        async def get(self):
            raise HTTPInternalServerError

    class TestView2(View):
        @DB(db_name="backend2").decorate
        async def get(self):
            raise HTTPInternalServerError

    app = web.Application()
    app.cleanup_ctx.append(Postgres(dsn="postgresql+asyncpg://postgres:postgres@localhost:5432/postgres",
                                    name="backend1").ctx)
    app.cleanup_ctx.append(Postgres(dsn="postgresql+asyncpg://postgres:postgres@localhost:5432/postgres",
                                    name="backend2").ctx)
    app.router.add_view('/tw1', TestView1)
    app.router.add_view('/tw2', TestView2)
    client = await aiohttp_client(app)
    with caplog.at_level(logging.DEBUG):
        resp = await client.get('/tw1')
        assert resp.status == 500
        resp = await client.get('/tw2')
        assert resp.status == 500

        assert "Opening session for backend1" in caplog.text
        assert "Closing session for backend1" in caplog.text
        assert "Opening session for backend2" in caplog.text
        assert "Closing session for backend2" in caplog.text
