import logging
import sys

import boto3
from aiobotocore.session import get_session
from aiohttp.web import Request, StreamResponse
from pydantic_settings import BaseSettings

from some_aiohttp_middleware import MiddlewareBase


class CognitoConfig(BaseSettings):
    pool: str = "local"
    region: str = "us-east-1"
    client: str = "local"

    class Config:
        env_prefix = "S_"


class CognitoSession:

    def __init__(self, *args, pool_id, client_id, pool_region, **kwargs):
        self._pool_id = pool_id
        assert self.pool_id, "No cognito pool provided via parameter or env"

        self._client_id = client_id
        assert self.client_id, "No cognito client provided via parameter or env"

        self._pool_region = pool_region
        assert self.pool_region, "No cognito pool region provided via parameter or env"

        self.session = None

    @property
    def pool_id(self):
        return self._pool_id

    @property
    def client_id(self):
        return self._client_id

    @property
    def pool_region(self):
        return self._pool_region

    async def __aenter__(self):
        return boto3.client('cognito-idp', region_name=self.pool_region)

    async def __aexit__(self, exc_type, exc_value, traceback):
        pass


class Cognito(MiddlewareBase):
    @staticmethod
    async def handle(request: Request, *args, **kwargs) -> Request:
        config = getattr(request.app, "config", {})
        cognito_config = config.cognito
        if not cognito_config:
            raise RuntimeError("No Cognito configuration found")

        request["cognito"] = CognitoSession(
            client_id=cognito_config.client,
            pool_id=cognito_config.pool,
            pool_region=cognito_config.region
        )

        logging.debug(
            f"Connected Cognito {cognito_config.pool} in {cognito_config.region}"
        )

    @staticmethod
    async def unhandle(
            request: Request, response: StreamResponse, *args, **kwargs
    ) -> StreamResponse:
        del request["cognito"]
        return response
