import operator
import re
from functools import reduce
from typing import Annotated, Any

from pydantic import AfterValidator, BaseModel, SecretStr, ValidationError

from .base import MiddlewareBase

from aiohttp.web_exceptions import (  # isort:skip
    HTTPInternalServerError,
    HTTPUnauthorized,
    HTTPUnprocessableEntity,
)


def bearer_check(v: Any) -> Any:
    try:
        return re.match(r"^Bearer\s([a-zA-Z\d]*)$", v).group(1)
    except AttributeError:
        raise HTTPUnprocessableEntity(reason="Malformed bearer token")


class Bearer(BaseModel):
    authorization: Annotated[str, AfterValidator(bearer_check)]


class AdminAuth(MiddlewareBase):

    @staticmethod
    async def handle(request, *args, admin_token=None, token_location=None, **kwargs):

        if token_location is None:
            token_location = ["admin_token"]

        try:
            admin_token = admin_token or reduce(
                operator.getitem,
                (
                    token_location
                    if isinstance(token_location, list)
                    else [token_location]
                ),
                dict(request.app.config),
            )
            admin_token = (
                admin_token.get_secret_value()
                if isinstance(admin_token, SecretStr)
                else admin_token
            )
        except (KeyError, TypeError, AttributeError):
            raise HTTPInternalServerError(
                reason="Missing configuration, either pass 'admin_token' or 'token_location'"
            )

        try:
            if (
                Bearer(
                    authorization=request.headers.getone("authorization", None)
                ).authorization
                != admin_token
            ):
                raise HTTPUnauthorized
        except ValidationError:
            raise HTTPUnprocessableEntity(reason="Missing authorization header")

        return request
