from aiohttp.web_exceptions import HTTPUnauthorized

from marshmallow import Schema, fields, post_load, ValidationError

from .base import MiddlewareBase


class AuthorizationSchema(Schema):
    authorization = fields.String(required=True)

    @post_load
    def validate(self, data, **_kwargs):
        try:
            auth = data.get('authorization', None)
            _, bearer_token = auth.split(" ")
            return {"token": bearer_token}

        except (ValueError, TypeError, AttributeError):
            raise ValidationError(message="Malformed authorization header")


class AdminAuthHandler(MiddlewareBase):

    @staticmethod
    async def handle(request, *args, **kwargs):

        admin_token = 'request.app["secrets"]["ADMIN_TOKEN"]'
        token = request['auth']['token']

        if token != admin_token:
            raise HTTPUnauthorized

        return request
