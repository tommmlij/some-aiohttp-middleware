import logging

import pytest
from aiohttp import web
from aiohttp.web import View
from aiohttp.web_exceptions import HTTPInternalServerError
from pydantic import BaseModel, PostgresDsn, conint

from some_aiohttp_middleware import DB, Postgres


class Config(BaseModel):
    dsn: PostgresDsn = PostgresDsn("postgresql+asyncpg://postgres:postgres@localhost:5432/postgres")
    pool_overflow: conint(ge=1, le=1000) = 10
    pool_size_max: conint(ge=1, le=1000) = 50
    pool_timeout: conint(ge=1, le=1000) = 120


@pytest.mark.asyncio
async def test_middleware(caplog, aiohttp_client):
    @DB(db_name="backend1").decorate
    class TestView1(View):
        async def get(self):
            raise HTTPInternalServerError

    @DB(db_name="backend2").decorate
    class TestView2(View):
        async def get(self):
            raise HTTPInternalServerError

    app = web.Application()
    app.config = Config()
    app.cleanup_ctx.append(
        Postgres(
            config=app.config,
            name="backend1",
        ).ctx
    )
    app.cleanup_ctx.append(
        Postgres(
            config=app.config,
            name="backend2",
        ).ctx
    )
    app.router.add_view("/tw1", TestView1)
    app.router.add_view("/tw2", TestView2)
    client = await aiohttp_client(app)
    with caplog.at_level(logging.DEBUG):
        resp = await client.get("/tw1")
        assert resp.status == 500
        resp = await client.get("/tw2")
        assert resp.status == 500

        assert "Opening session for backend1" in caplog.text
        assert "Closing session for backend1" in caplog.text
        assert "Opening session for backend2" in caplog.text
        assert "Closing session for backend2" in caplog.text
