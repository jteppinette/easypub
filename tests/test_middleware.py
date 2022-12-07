import pytest

from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.responses import Response
from starlette.routing import Route
from starlette.testclient import TestClient

from easypub.middleware import CacheControlMiddleware


class TestCacheControl:
    @pytest.mark.parametrize(
        "method, status_code, expected",
        [
            ("get", 200, True),
            ("get", 304, False),
            ("get", 500, False),
            ("post", 200, False),
            ("head", 200, False),
        ],
    )
    def test_applied(self, method, status_code, expected):
        def hello(request):
            return Response(status_code=status_code)

        app = Starlette(
            middleware=[Middleware(CacheControlMiddleware, max_age="1s")],
            routes=[Route("/", hello)],
        )

        response = TestClient(app).request(method, "/")

        assert ("cache-control" in response.headers) is expected

        if expected:
            assert response.headers["cache-control"] == "max-age=1"

    @pytest.mark.parametrize("enabled", [True, False])
    def test_globally_disabled(self, enabled):
        def hello(request):
            return Response()

        app = Starlette(
            middleware=[Middleware(CacheControlMiddleware, max_age="1s")],
            routes=[Route("/", hello)],
        )
        app.state.cache_control = enabled

        response = TestClient(app).get("/")

        assert ("cache-control" in response.headers) is enabled
