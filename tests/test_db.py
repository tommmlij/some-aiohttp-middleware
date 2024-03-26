import pytest
from aiohttp import web
from aiohttp.web import View
from pydantic import BaseModel, PostgresDsn

from some_aiohttp_middleware import DB, Postgres


class WrongConfig(BaseModel):
    pass


@pytest.mark.asyncio
async def test_db_missing_dsn():
    app = web.Application()
    app.config = WrongConfig()
    with pytest.raises(Exception) as exc_info:
        app.cleanup_ctx.append(Postgres(app.config).ctx)
    assert isinstance(exc_info.value, Exception)
    assert "DSN or location of DSN in the configuration needed" == str(exc_info.value)


class RightConfig(BaseModel):
    dsn: PostgresDsn = PostgresDsn("postgresql+asyncpg://postgres:postgres@localhost:5432/postgres")


@pytest.mark.asyncio
async def test_middleware(aiohttp_client):
    @DB(db_name="does_not_exists").decorate
    class TestView1(View):
        async def get(self):
            pass

    app = web.Application()
    app.config = RightConfig()
    app.cleanup_ctx.append(Postgres(config=app.config).ctx)
    app.router.add_view("/tw1", TestView1)
    client = await aiohttp_client(app)
    resp = await client.get("/tw1")
    assert resp.status == 500
    assert "DB session not found" == resp.reason
