import operator
from base64 import urlsafe_b64decode
from functools import reduce
from typing import Any, Optional

from pydantic import BaseModel, ValidationError, model_validator

from .base import MiddlewareBase

from aiohttp.web_exceptions import (  # isort:skip
    HTTPInternalServerError,
    HTTPUnauthorized,
    HTTPUnprocessableEntity,
    HTTPBadRequest,
)


class BasicAuthModel(BaseModel):
    user: str
    password: str

    @model_validator(mode="before")
    def decode_basic_auth(self) -> Any:
        try:
            decode = urlsafe_b64decode(
                self.replace("Basic ", "").encode("utf-8")
            ).decode("utf-8")
        except ValueError:
            raise HTTPBadRequest(text="Malformed Basic Auth header")
        try:
            output = {
                "user": (decode.split(":"))[0],
                "password": (decode.split(":"))[1],
            }
        except IndexError:
            raise HTTPBadRequest(
                text="Malformed Basic Auth payload (should be username:password)"
            )
        return output


class BasicAuth(MiddlewareBase):

    @staticmethod
    async def handle(
        request, *args, users: Optional[dict] = None, users_location=None, **kwargs
    ):

        if users_location is None:
            users_location = ["users"]

        try:
            users = users or reduce(
                operator.getitem,
                (
                    users_location
                    if isinstance(users_location, list)
                    else [users_location]
                ),
                dict(request.app.config),
            )
        except (KeyError, TypeError, AttributeError):
            raise HTTPInternalServerError(
                reason="Missing configuration, either pass 'users' or 'users_location'"
            )

        try:
            auth = BasicAuthModel.parse_obj(
                request.headers.getone("authorization", None)
            )
            if auth.user not in users or users[auth.user] != auth.password:
                raise HTTPUnauthorized
            request.authorization = auth.model_dump()
        except ValidationError:
            raise HTTPUnprocessableEntity(reason="Missing authorization header")

        return request
