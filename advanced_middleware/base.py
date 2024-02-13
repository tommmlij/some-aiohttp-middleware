import asyncio
from abc import ABC, abstractmethod
from functools import wraps, partial
from typing import Callable

from aiohttp import hdrs
from aiohttp.web import View


class HybridMethod(object):
    """
    Decorator to create a hybrid "method", meaning you can call the function from
    the class or an object.

            class T():
                @HybridMethod
                def my_function(self_or_cls):
                    pass

            T.my_function()
            t = T()
            t.my_function()

    The class HybridMethod acts as a descriptor. On initialization the decorated function is
    stored in the class.
    When the __get__ method of the descriptor is called, it is checked, if it was called
    bound or unbound. In case of the later, the context is set to the class.

    """

    def __init__(self, func):
        self.func = func

    def __get__(self, obj, cls):
        context = obj if obj is not None else cls

        @wraps(self.func)
        def hybrid(*args, **kwargs):
            return self.func(context, *args, **kwargs)

        hybrid.__func__ = self.func
        hybrid.__self__ = context

        return hybrid


class MiddlewareBase(ABC):
    args = ()
    kwargs = {}

    def __init__(self, /, *args, **kwargs):
        super().__init__()

        # Add all args and kwargs to the object
        self.args = args
        self.kwargs = kwargs

    @staticmethod
    @abstractmethod
    async def handle(request, **kwargs):
        pass

    @staticmethod
    async def unhandle(request, response, **kwargs):
        return response

    @HybridMethod
    def decorate(cls_or_self, obj=None, **kwargs):

        if obj is None:  # The decorator was "called", e.g. to add kwargs
            # We add the kwargs via partial and return the decorator function
            return partial(cls_or_self.decorate, **kwargs)

        if isinstance(obj, type):  # class
            # The decorator was used on a class
            assert issubclass(obj, View)

            class NewClass(obj):
                def __init__(self, *i_args, **i_kwargs):
                    super().__init__(*i_args, *i_kwargs)

                def __getattribute__(self, name):
                    # Get the original method
                    original_method = super().__getattribute__(name)

                    # Check if the attribute is one of the View method to be decorated
                    if (callable(original_method)
                            and asyncio.iscoroutinefunction(original_method)
                            and str(name).upper() in hdrs.METH_ALL):

                        @wraps(obj)
                        async def wrapper():

                            await cls_or_self.handle(request=self.request, **(cls_or_self.kwargs | kwargs))
                            response = await obj(self.request)
                            await cls_or_self.unhandle(request=self.request, response=response,
                                                       **(cls_or_self.kwargs | kwargs))
                            return response

                        return wrapper

                    else:
                        return original_method

            return NewClass

        else:  # function
            @wraps(obj)
            async def wrapper_function(view):

                await cls_or_self.handle(request=view.request, **(cls_or_self.kwargs | kwargs))
                response = await obj(view)
                await cls_or_self.unhandle(request=view.request, response=response,
                                           **(cls_or_self.kwargs | kwargs))
                return response

            return wrapper_function
