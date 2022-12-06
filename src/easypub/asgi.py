from collections import defaultdict
from http import HTTPStatus

from pydantic import ValidationError
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.gzip import GZipMiddleware
from starlette.responses import JSONResponse
from starlette.routing import Mount, Route
from starlette.staticfiles import StaticFiles

from easypub import config
from easypub.endpoints import (
    HealthEndpoint,
    HomeEndpoint,
    PublishEndpoint,
    ReadEndpoint,
)
from easypub.middleware import TimeoutMiddleware

routes = [
    Route("/", endpoint=HomeEndpoint),
    Mount("/static", app=StaticFiles(directory=config.static.directory), name="static"),
    Mount(
        "/api",
        routes=[
            Route("/health", endpoint=HealthEndpoint),
            Route("/publish", endpoint=PublishEndpoint),
        ],
    ),
    Route("/{slug:str}", endpoint=ReadEndpoint),
]


async def validation_error_handler(request, exc):
    errors = defaultdict(list)

    for error in exc.errors():
        path = ".".join(error["loc"])
        errors[path].append(error["msg"])

    return JSONResponse(errors, status_code=HTTPStatus.UNPROCESSABLE_ENTITY)


exception_handlers = {
    ValidationError: validation_error_handler,
    RateLimitExceeded: _rate_limit_exceeded_handler,
}

app = Starlette(
    debug=config.debug,
    middleware=[
        Middleware(TimeoutMiddleware, timeout=config.request_timeout),
        Middleware(GZipMiddleware),
    ],
    routes=routes,
    exception_handlers=exception_handlers,
)

app.state.limiter = config.limiter
