import pytest
from aiohttp import web
from aiohttp.web import View

from some_aiohttp_middleware import DB, Postgres


@pytest.mark.asyncio
async def test_db_missing_dsn():
    app = web.Application()
    with pytest.raises(Exception) as exc_info:
        app.cleanup_ctx.append(Postgres().ctx)
    assert isinstance(exc_info.value, AssertionError)
    assert "DSN or location of DSN in the configuration needed" == str(exc_info.value)


@pytest.mark.asyncio
async def test_middleware(aiohttp_client):
    @DB(db_name="does_not_exists").decorate
    class TestView1(View):
        async def get(self):
            pass

    app = web.Application()
    app.cleanup_ctx.append(Postgres(dsn="postgresql+asyncpg://postgres:postgres@localhost:5432/postgres").ctx)
    app.router.add_view('/tw1', TestView1)
    client = await aiohttp_client(app)
    resp = await client.get('/tw1')
    assert resp.status == 500
    assert "DB session not found" == resp.reason
