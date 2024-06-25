import logging
import os
from io import BytesIO

import pytest
from aiohttp import web
from aiohttp.web import HTTPOk, Request, Response, View
from aiohttp_middlewares import error_context
from pydantic import BaseModel

from some_aiohttp_middleware import DynamoDB, DynamoDBConfig


class Config(BaseModel):
    dynamodb: dict[str, DynamoDBConfig] = {
        "1": DynamoDBConfig(region="eu-west-1", table=os.environ["SOME_TABLE"]),
        "2": DynamoDBConfig(region="eu-west-1", table=os.environ["SOME_OTHER_TABLE"]),
    }


@pytest.mark.asyncio
async def test_middleware(caplog, aiohttp_client):
    @DynamoDB.decorate
    class TestView1(View):
        async def get(self):
            # TODO: Write test
            raise HTTPOk

    @DynamoDB.decorate
    class TestView2(View):
        async def get(self):
            # TODO: Write test
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
