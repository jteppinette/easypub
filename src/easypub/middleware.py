import asyncio

from starlette.datastructures import MutableHeaders
from starlette.responses import Response

from easypub.caching import build_cache_control


class TimeoutMiddleware:
    def __init__(self, app, timeout):
        self.app = app
        self.timeout = timeout

    async def __call__(self, scope, receive, send):
        if scope["type"] == "lifespan":
            return await self.app(scope, receive, send)

        try:
            return await asyncio.wait_for(
                self.app(scope, receive, send), timeout=self.timeout
            )
        except asyncio.TimeoutError:
            response = Response(status_code=408)
            return await response(scope, receive, send)


class CacheControlMiddleware:
    def __init__(self, app, **options):
        self.app = app
        self.value = build_cache_control(**options)

    async def __call__(self, scope, receive, send):
        try:
            if not scope["app"].state.cache_control:
                return await self.app(scope, receive, send)
        except (AttributeError, KeyError):
            pass

        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        if scope["method"] != "GET":
            return await self.app(scope, receive, send)

        async def modify(message):
            if message["type"] != "http.response.start":
                return await send(message)

            if message["status"] != 200:
                return await send(message)

            headers = MutableHeaders(scope=message)
            headers["Cache-Control"] = self.value

            await send(message)

        await self.app(scope, receive, modify)
