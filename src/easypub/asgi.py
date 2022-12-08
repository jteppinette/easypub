from collections import defaultdict
from http import HTTPStatus

from pydantic import ValidationError
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.gzip import GZipMiddleware
from starlette.responses import JSONResponse

from easypub import config
from easypub.middleware import TimeoutMiddleware
from easypub.routes import routes


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
app.state.cache_control = config.cache_control
