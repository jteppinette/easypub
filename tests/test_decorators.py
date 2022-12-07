import pytest

from starlette.applications import Starlette
from starlette.endpoints import HTTPEndpoint
from starlette.responses import Response
from starlette.routing import Route
from starlette.testclient import TestClient

from easypub.decorators import cache_control


class TestCacheControl:
    CASES = [
        ("get", 200, True),
        ("get", 304, False),
        ("get", 500, False),
        ("post", 200, False),
        ("head", 200, False),
    ]

    def run(self, endpoint, method, status_code, expected):
        app = Starlette(
            routes=[Route("/", endpoint)],
        )

        response = TestClient(app).request(method, "/")

        assert ("cache-control" in response.headers) is expected

        if expected:
            assert response.headers["cache-control"] == "max-age=1"

    @pytest.mark.parametrize("method, status_code, expected", CASES)
    def test_sync(self, method, status_code, expected):
        @cache_control(max_age="1s")
        def hello(request):
            return Response(status_code=status_code)

        self.run(hello, method, status_code, expected)

    @pytest.mark.parametrize("method, status_code, expected", CASES)
    def test_async(self, method, status_code, expected):
        @cache_control(max_age="1s")
        async def hello(request):
            return Response(status_code=status_code)

        self.run(hello, method, status_code, expected)

    @pytest.mark.parametrize("method, status_code, expected", CASES)
    def test_endpoint(self, method, status_code, expected):
        class Hello(HTTPEndpoint):
            @cache_control(max_age="1s")
            async def get(self, request):
                return Response(status_code=status_code)

            @cache_control(max_age="1s")
            async def post(self, request):
                return Response(status_code=status_code)

            @cache_control(max_age="1s")
            async def head(self, request):
                return Response(status_code=status_code)

        self.run(Hello, method, status_code, expected)

    @pytest.mark.parametrize("enabled", [True, False])
    def test_globally_disabled(self, enabled):
        @cache_control(max_age="1s")
        def hello(request):
            return Response()

        app = Starlette(
            routes=[Route("/", hello)],
        )
        app.state.cache_control = enabled

        response = TestClient(app).get("/")

        assert ("cache-control" in response.headers) is enabled
