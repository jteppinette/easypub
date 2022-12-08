from http import HTTPStatus
from unittest.mock import AsyncMock

import pytest

from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.routing import Router
from starlette.templating import Jinja2Templates
from starlette.testclient import TestClient

from easypub.endpoints import crypt_context
from easypub.routes import routes


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


app = Router(routes=routes)


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
        redis_hgetall.return_value = {b"secret_hash": b"s", b"title": b"Test"}
        s3_get_object.return_value = MockS3Response(text="c", status=200)

        response = client.get("/test")

        assert response.status_code == HTTPStatus.OK

        assert isinstance(response.context["request"], Request)
        assert response.context["title"] == "Test"
        assert response.context["content"] == "c"


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
            "/api/publish", json={"title": "Test", "content": "<p>test</p>"}
        )
        assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY

        data = response.json()
        assert data["title"] == ["is already being used"]

    def test_publish(self, client, redis_exists, redis_hset, s3_put_object):
        redis_exists.return_value = False

        response = client.post(
            "/api/publish", json={"title": "Test", "content": "<script>"}
        )

        redis_hset.assert_awaited_once()
        redis_hset.await_args.args == ["metadata:test"]

        assert len(redis_hset.await_args.kwargs) == 1
        assert "mapping" in redis_hset.await_args.kwargs

        mapping = redis_hset.await_args.kwargs["mapping"]
        assert isinstance(mapping["secret_hash"], str)
        assert mapping["title"] == "Test"

        s3_put_object.assert_awaited_once()

        assert response.status_code == HTTPStatus.OK

        data = response.json()
        assert isinstance(data["secret"], str)
        assert isinstance(data["url"], str)

        assert crypt_context.verify(data["secret"], mapping["secret_hash"])


class TestUpdateEndpoint:
    @pytest.fixture
    def redis_hgetall(self, config, monkeypatch):
        mock = AsyncMock()
        monkeypatch.setattr(config.redis, "hgetall", mock)
        return mock

    @pytest.fixture
    def s3_put_object(self, config, monkeypatch):
        mock = AsyncMock()
        monkeypatch.setattr(config.s3, "put_object", mock)
        return mock

    def test_not_found(self, client, redis_hgetall):
        redis_hgetall.return_value = None

        with pytest.raises(HTTPException, match="NOT_FOUND"):
            client.post(
                "/api/test/update", json={"secret": "secret", "content": "<p>test</p>"}
            )

    def test_incorrect_password(self, client, redis_hgetall):
        redis_hgetall.return_value = {
            b"secret_hash": b"$2b$12$kbGqdxpfbOCDxiVO7Dupee635ot/7PxgaQtStZwI7Lb4aQqLoNI8S"
        }

        response = client.post(
            "/api/test/update", json={"secret": "incorrect", "content": "<p>test</p>"}
        )

        assert response.status_code == 422

    def test_ok(self, client, redis_hgetall, s3_put_object):
        redis_hgetall.return_value = {
            b"secret_hash": b"$2b$12$kbGqdxpfbOCDxiVO7Dupee635ot/7PxgaQtStZwI7Lb4aQqLoNI8S"
        }

        response = client.post(
            "/api/test/update",
            json={
                "secret": "-2pTK-KBRQn7IDNMzm3oJBbAiI1QU_jC_fAz9TuZI18",
                "content": "<p>test</p>",
            },
        )

        s3_put_object.assert_awaited_once()

        assert response.status_code == 200

        data = response.json()

        assert len(data) == 1
        assert "test" in data["url"]


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
