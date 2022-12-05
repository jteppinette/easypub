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
    def hgetall(self, config, monkeypatch):
        mock = AsyncMock()
        monkeypatch.setattr(config.redis, "hgetall", mock)
        return mock

    def test_not_found(self, client):
        with pytest.raises(HTTPException, match="NOT_FOUND"):
            client.get("/test")

    def test_read(self, client, hgetall):
        hgetall.return_value = {b"content": b"c", b"secret_hash": b"s"}

        response = client.get("/test")

        assert response.status_code == HTTPStatus.OK

        assert isinstance(response.context["request"], Request)
        assert response.context["title"] == "Test"
        assert response.context["content"] == "c"
        assert response.context["secret_hash"] == "s"


class TestPublishEndpoint:
    @pytest.fixture(autouse=True)
    def exists(self, config, monkeypatch):
        mock = AsyncMock()
        monkeypatch.setattr(config.redis, "exists", mock)
        return mock

    @pytest.fixture(autouse=True)
    def hset(self, config, monkeypatch):
        mock = AsyncMock()
        monkeypatch.setattr(config.redis, "hset", mock)
        return mock

    def test_not_unique(self, client, exists):
        exists.return_value = True

        response = client.post(
            "/api/publish", json={"slug": "test", "content": "<p>test</p>"}
        )
        assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY

        data = response.json()
        assert data["slug"] == ["is used by another post"]

    def test_publish(self, client, exists, hset):
        exists.return_value = False

        response = client.post(
            "/api/publish", json={"slug": "test", "content": "<script>"}
        )

        hset.assert_awaited_once()
        hset.await_args.args == ["post:test"]

        assert len(hset.await_args.kwargs) == 1
        assert "mapping" in hset.await_args.kwargs

        mapping = hset.await_args.kwargs["mapping"]
        assert mapping["content"] == "&lt;script&gt;"
        assert isinstance(mapping["secret_hash"], str)

        assert response.status_code == HTTPStatus.OK

        data = response.json()
        assert isinstance(data["secret"], str)
        assert isinstance(data["url"], str)

        assert crypt_context.verify(data["secret"], mapping["secret_hash"])


class TestHealthEndpoint:
    @pytest.fixture
    def ping(self, config, monkeypatch):
        mock = AsyncMock()
        monkeypatch.setattr(config.redis, "ping", mock)
        return mock

    def test_ok(self, client, ping):
        ping.return_value = True

        response = client.get("/api/health")
        assert response.status_code == HTTPStatus.OK
        assert response.json() == {"redis": True}
