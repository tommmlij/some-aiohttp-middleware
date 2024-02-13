import asyncio
from abc import ABC, abstractmethod
from functools import wraps, partial

from aiohttp import hdrs


def wrapper_factory(func, request, handler, unhandler, kwargs_class, **kwargs_method):
    @wraps(func)
    async def wrapper(*args):
        await handler(request, *args, **(kwargs_class | kwargs_method))
        response = await func(*args)
        await unhandler(request, response, *args, **(kwargs_class | kwargs_method))
        return response

    return wrapper


class HybridMethod(object):
    def __init__(self, func):
        self.func = func

    def __get__(self, obj, cls):
        context = obj if obj is not None else cls

        @wraps(self.func)
        def hybrid(*args, **kw):
            return self.func(context, *args, **kw)

        hybrid.__func__ = self.func
        hybrid.__self__ = context

        return hybrid


class MiddlewareBase(ABC):
    kwargs = {}
    request = None

    def __init__(self, /, **kwargs):
        super().__init__()

        # Add all kwargs to the object
        self.kwargs = kwargs

    @staticmethod
    @abstractmethod
    async def handle(request, *args, **kwargs):
        pass

    @staticmethod
    async def unhandle(request, response, *args, **kwargs):
        return response

    @HybridMethod
    def decorate(cls_or_self, obj=None, **kwargs):

        if obj is None:
            return partial(cls_or_self.decorate, **kwargs)

        if isinstance(obj, type):  # class
            class NewClass(obj):
                def __init__(self, request, **i_kwargs):
                    super().__init__(request, **i_kwargs)

                def __getattribute__(self, name):
                    # Get the original method
                    original_method = super().__getattribute__(name)

                    # Check if the attribute is a method and not a special method like __init__
                    if (callable(original_method)
                            and asyncio.iscoroutinefunction(original_method)
                            and str(name).upper() in hdrs.METH_ALL):

                        return wrapper_factory(original_method, cls_or_self.request, cls_or_self.handle,
                                               cls_or_self.unhandle,
                                               cls_or_self.kwargs, **kwargs)
                    else:
                        return original_method

            return NewClass

        else:  # function
            return wrapper_factory(obj, cls_or_self.request, cls_or_self.handle, cls_or_self.unhandle,
                                   cls_or_self.kwargs, **kwargs)
