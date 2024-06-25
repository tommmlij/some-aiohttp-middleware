import logging
import sys

from aiobotocore.session import get_session
from aiohttp.web import Request, StreamResponse
from pydantic_settings import BaseSettings

from some_aiohttp_middleware import MiddlewareBase


class DynamoDBConfig(BaseSettings):

    def __init__(self, name: str = "default", region: str = "us-east-1", **kwargs):
        super().__init__(
            _env_prefix=f"S_{name.upper()}_" if name else "S_",
            name=name,
            region=region,
            **kwargs,
        )

    table: str
    name: str
    region: str = "us-east-1"


class DynamoDBSession:

    def __init__(self, *args, table_name, table_region, **kwargs):
        self._table_name = table_name
        assert self.table_name, "No dynamodb table name provided via parameter or env"

        self._table_region = table_region
        assert self.table_region, "No dynamodb table region provided via parameter or env"

        self.session = None

    @property
    def table_name(self):
        return self._table_name

    @property
    def table_region(self):
        return self._table_region

    async def __aenter__(self):
        session = get_session()
        self.session = session.create_client('dynamodb', region_name=self.table_region)
        return await self.session.__aenter__()

    async def __aexit__(self, exc_type, exc_value, traceback):
        if self.session:
            await self.session.__aexit__(exc_type, exc_value, traceback)


class DynamoDB(MiddlewareBase):
    @staticmethod
    async def handle(request: Request, *args, **kwargs) -> Request:
        config = getattr(request.app, "config", {})
        dynamodb_configs = config.dynamodb
        if not dynamodb_configs:
            raise RuntimeError("No DynamoDB configuration found")

        if not request.get("dynamodb"):
            request["dynamodb"] = {}

        for name, config in dynamodb_configs.items():
            request["dynamodb"][name] = DynamoDBSession(
                table_name=config.table,
                table_region=config.region)
            logging.debug(
                f"Connected table {name} to {config.table} in {config.region}"
            )
        return request

    @staticmethod
    async def unhandle(
            request: Request, response: StreamResponse, *args, **kwargs
    ) -> StreamResponse:
        for k, v in request["dynamodb"].items():
            await v.__aexit__(*sys.exc_info())
            logging.debug(f"closed session to table in {k}")
        return response
