import functools
import inspect
import typing
from typing import Callable

from starlette._utils import is_async_callable
from starlette.requests import Request
from starlette.responses import Response

from easypub.caching import build_cache_control


def cache_control(**options) -> Callable[[Callable], Callable]:
    value = build_cache_control(**options)

    def apply(request: Request, response: Response) -> Response:
        try:
            if not request.app.state.cache_control:
                return response
        except (AttributeError, KeyError):
            pass

        if request.method != "GET":
            return response

        if response.status_code != 200:
            return response

        response.headers["Cache-Control"] = value

        return response

    def decorator(func: Callable) -> Callable:
        sig = inspect.signature(func)

        if "request" not in sig.parameters:
            raise AssertionError(
                f'No "request" argument on function "{func}". This decorator only supports http.'
            )

        request_idx = list(sig.parameters.keys()).index("request")

        def get_request(*args, **kwargs):
            request = kwargs.get(
                "request", args[request_idx] if request_idx < len(args) else None
            )
            if not isinstance(request, Request):
                raise AssertionError(
                    f"request must be of type Request not {type(request)}"
                )
            assert isinstance(request, Request)
            return request

        if is_async_callable(func):

            @functools.wraps(func)
            async def async_wrapper(
                *args: typing.Any, **kwargs: typing.Any
            ) -> Response:
                request = get_request(*args, **kwargs)
                return apply(request, await func(*args, **kwargs))

            return async_wrapper

        else:

            @functools.wraps(func)
            def sync_wrapper(*args: typing.Any, **kwargs: typing.Any) -> Response:
                request = get_request(*args, **kwargs)
                return apply(request, func(*args, **kwargs))

            return sync_wrapper

    return decorator
