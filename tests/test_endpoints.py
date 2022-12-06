from http import HTTPStatus
from unittest.mock import AsyncMock

import pytest

from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.routing import Route, Router
from starlette.templating import Jinja2Templates
from starlette.testclient import TestClient

from easypub.endpoints import (
    HealthEndpoint,
    HomeEndpoint,
    PublishEndpoint,
    ReadEndpoint,
    crypt_context,
)


class MockS3Response:
    def __init__(self, text, status):
        self._text = text
        self.status = status

    async def text(self):
        return self._text

    async def __aexit__(self, exc_type, exc, tb):
        pass

    async def __aenter__(self):
        return self


app = Router(
    routes=[
        Route("/", endpoint=HomeEndpoint),
        Route("/{slug:str}", endpoint=ReadEndpoint),
        Route("/api/publish", endpoint=PublishEndpoint),
        Route("/api/health", endpoint=HealthEndpoint),
    ]
)


@pytest.fixture
def client(config):
    config.templates = Jinja2Templates(directory=config.base_dir / "templates")
    config.templates.env.globals["static_url_for"] = lambda name, path: path
    return TestClient(app)


class TestHomeEndpoint:
    def test_ok(self, client):
        response = client.get("/")
        assert response.status_code == HTTPStatus.OK


class TestReadEndpoint:
    @pytest.fixture
    def redis_hgetall(self, config, monkeypatch):
        mock = AsyncMock()
        monkeypatch.setattr(config.redis, "hgetall", mock)
        return mock

    @pytest.fixture
    def s3_get_object(self, config, monkeypatch):
        mock = AsyncMock()
        monkeypatch.setattr(config.s3, "get_object", mock)
        return mock

    def test_not_found(self, client):
        with pytest.raises(HTTPException, match="NOT_FOUND"):
            client.get("/test")

    def test_read(self, client, redis_hgetall, s3_get_object):
        redis_hgetall.return_value = {b"secret_hash": b"s"}
        s3_get_object.return_value = MockS3Response(text="c", status=200)

        response = client.get("/test")

        assert response.status_code == HTTPStatus.OK

        assert isinstance(response.context["request"], Request)
        assert response.context["title"] == "Test"
        assert response.context["content"] == "c"
        assert response.context["secret_hash"] == "s"


class TestPublishEndpoint:
    @pytest.fixture
    def redis_exists(self, config, monkeypatch):
        mock = AsyncMock()
        monkeypatch.setattr(config.redis, "exists", mock)
        return mock

    @pytest.fixture
    def redis_hset(self, config, monkeypatch):
        mock = AsyncMock()
        monkeypatch.setattr(config.redis, "hset", mock)
        return mock

    @pytest.fixture
    def s3_put_object(self, config, monkeypatch):
        mock = AsyncMock()
        monkeypatch.setattr(config.s3, "put_object", mock)
        return mock

    def test_not_unique(self, client, redis_exists):
        redis_exists.return_value = True

        response = client.post(
            "/api/publish", json={"slug": "test", "content": "<p>test</p>"}
        )
        assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY

        data = response.json()
        assert data["slug"] == ["is used by another post"]

    def test_publish(self, client, redis_exists, redis_hset, s3_put_object):
        redis_exists.return_value = False

        response = client.post(
            "/api/publish", json={"slug": "test", "content": "<script>"}
        )

        redis_hset.assert_awaited_once()
        redis_hset.await_args.args == ["metadata:test"]

        assert len(redis_hset.await_args.kwargs) == 1
        assert "mapping" in redis_hset.await_args.kwargs

        mapping = redis_hset.await_args.kwargs["mapping"]
        assert isinstance(mapping["secret_hash"], str)

        s3_put_object.assert_awaited_once()

        assert response.status_code == HTTPStatus.OK

        data = response.json()
        assert isinstance(data["secret"], str)
        assert isinstance(data["url"], str)

        assert crypt_context.verify(data["secret"], mapping["secret_hash"])


class TestHealthEndpoint:
    @pytest.fixture
    def redis_ping(self, config, monkeypatch):
        mock = AsyncMock()
        monkeypatch.setattr(config.redis, "ping", mock)
        return mock

    def test_ok(self, client, redis_ping):
        redis_ping.return_value = True

        response = client.get("/api/health")
        assert response.status_code == HTTPStatus.OK
        assert response.json() == {"redis": True}
