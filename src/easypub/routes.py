from starlette.middleware import Middleware
from starlette.routing import Mount, Route
from starlette.staticfiles import StaticFiles

from easypub import config
from easypub.endpoints import (
    AdminEndpoint,
    HealthEndpoint,
    HomeEndpoint,
    PublishEndpoint,
    ReadEndpoint,
    UpdateEndpoint,
)
from easypub.middleware import CacheControlMiddleware

routes = [
    Route("/", endpoint=HomeEndpoint, name="home"),
    Mount(
        "/static",
        app=StaticFiles(directory=config.static.directory),
        middleware=[Middleware(CacheControlMiddleware, immutable=True)],
        name="static",
    ),
    Mount(
        "/api",
        routes=[
            Route("/health", endpoint=HealthEndpoint, name="health"),
            Route("/publish", endpoint=PublishEndpoint, name="publish"),
            Route("/{slug:str}/update", endpoint=UpdateEndpoint, name="update"),
        ],
    ),
    Route("/{slug:str}", endpoint=ReadEndpoint, name="read"),
    Route("/{slug:str}/admin", endpoint=AdminEndpoint, name="admin"),
]
