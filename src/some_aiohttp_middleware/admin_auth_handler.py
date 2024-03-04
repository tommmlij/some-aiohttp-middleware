import operator
from functools import reduce

from aiohttp.web_exceptions import HTTPUnauthorized, HTTPUnprocessableEntity, HTTPInternalServerError

from marshmallow import Schema, fields, post_load, ValidationError, EXCLUDE

from .base import MiddlewareBase


class AuthorizationSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    authorization = fields.String(required=True)

    def handle_error(self, exc, data, **kwargs):
        raise HTTPUnprocessableEntity(reason=exc)

    @post_load
    def validate(self, data, **_kwargs):
        try:
            auth = data.get('authorization', None)
            _, bearer_token = auth.split(" ")
            return bearer_token

        except (ValueError, TypeError, AttributeError):
            raise ValidationError(field_name="authorization", message="Malformed authorization header")


class AdminAuthHandler(MiddlewareBase):

    @staticmethod
    async def handle(request, *args,
                     admin_token=None,
                     token_location=None, **kwargs):

        assert not (admin_token is None and token_location is None), \
            "Admin token or location in the configuration needed"

        try:
            admin_token = admin_token or reduce(operator.getitem, token_location, request.app)
        except (KeyError, TypeError):
            raise HTTPInternalServerError(reason="Missing configuration")

        if admin_token != AuthorizationSchema().load(request.headers):
            raise HTTPUnauthorized

        return request
