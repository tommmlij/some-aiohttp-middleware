import logging
import sys

from aioboto3 import Session
from aiohttp.web import Request, StreamResponse
from pydantic_settings import BaseSettings

from some_aiohttp_middleware import MiddlewareBase


class S3Config(BaseSettings):

    def __init__(self, name: str = "default", region: str = "us-east-1", **kwargs):
        super().__init__(
            _env_prefix=f"S_{name.upper()}_" if name else "S_",
            name=name,
            region=region,
            **kwargs,
        )

    bucket: str
    name: str
    region: str = "us-east-1"


class S3(MiddlewareBase):
    @staticmethod
    async def handle(request: Request, *args, **kwargs) -> Request:
        app = request.app
        config = getattr(request.app, "config")

        if not config:
            raise RuntimeError("No S3 configuration found")

        try:
            s3_configs = getattr(config, "s3")
        except AttributeError:
            raise RuntimeError("S3 bucket definition needed in the configuration")

        for s3_config in s3_configs:
            if not app.get("s3"):
                s3 = (
                    await Session()
                    .resource("s3", region_name=s3_config.region)
                    .__aenter__()
                )
                app["s3"] = {
                    "sessions": {s3_config.region: s3},
                    "buckets": {s3_config.name: await s3.Bucket(s3_config.bucket)},
                }
            else:
                if s3_config.region in app["s3"]["sessions"]:
                    s3 = app["s3"]["sessions"][s3_config.region]
                else:
                    s3 = (
                        await Session()
                        .resource("s3", region_name=s3_config.region)
                        .__aenter__()
                    )
                    app["s3"]["sessions"][s3_config.region] = s3
                app["s3"]["buckets"][s3_config.name] = await s3.Bucket(s3_config.bucket)
            logging.debug(
                f"Connected bucket {s3_config.name} to {s3_config.bucket} in {s3_config.region}"
            )
        return request

    @staticmethod
    async def unhandle(
        request: Request, response: StreamResponse, *args, **kwargs
    ) -> StreamResponse:
        for k, v in request.app["s3"]["sessions"].items():
            await v.__aexit__(*sys.exc_info())
            logging.debug(f"closed session to buckets in {k}")
        return response
