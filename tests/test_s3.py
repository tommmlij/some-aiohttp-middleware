import logging
import os
from io import BytesIO

import pytest
from aiohttp import web
from aiohttp.web import HTTPOk, Request, Response, View
from aiohttp_middlewares import error_context
from pydantic import BaseModel

from some_aiohttp_middleware import S3, S3Config


class Config(BaseModel):
    s3: list[S3Config] = [
        S3Config("1", region="eu-west-1", bucket=os.environ["SOME_BUCKET"]),
        S3Config("2", region="eu-west-1", bucket=os.environ["SOME_OTHER_BUCKET"]),
    ]


@pytest.mark.asyncio
async def test_middleware(caplog, aiohttp_client):
    @S3.decorate
    class TestView1(View):
        async def get(self):
            f = BytesIO()
            await self.request.app["s3"]["buckets"]["1"].download_fileobj(
                os.environ["SOME_KEY"], f
            )
            content = f.getvalue().decode("utf-8")
            assert isinstance(content, str)
            raise HTTPOk

    @S3.decorate
    class TestView2(View):
        async def get(self):
            f = BytesIO()
            await self.request.app["s3"]["buckets"]["2"].download_fileobj(
                os.environ["SOME_OTHER_KEY"], f
            )
            content = f.getvalue().decode("utf-8")
            assert isinstance(content, str)
            raise HTTPOk

    async def api_error(request: Request) -> Response:
        with error_context(request) as context:
            print(
                f"\n{context.err}\n{context.message}\n{context.data}\n{context.status}\n"
            )
        return Response()

    app = web.Application(
        middlewares=[
            # error_middleware(ignore_exceptions=HTTPOk, default_handler=api_error)
        ]
    )
    app.config = Config()
    app.router.add_view("/tw1", TestView1)
    app.router.add_view("/tw2", TestView2)
    client = await aiohttp_client(app)
    with caplog.at_level(logging.INFO):
        resp1 = await client.get("/tw1")
        resp2 = await client.get("/tw2")

        if resp1.status != 200 or resp2.status != 200:
            print("CAP IN")
            for record in caplog.records:
                print(record.message)
            print("CAP OUT")
            assert resp1.status == 200
            assert resp2.status == 200
