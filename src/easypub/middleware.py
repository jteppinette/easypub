import asyncio

from starlette.responses import Response


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
