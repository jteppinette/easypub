from copy import deepcopy
from http import HTTPStatus

import pytest

from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.routing import Router
from starlette.testclient import TestClient

from easypub.endpoints import crypt_context
from easypub.routes import routes

from . import mocks


@pytest.fixture
def app():
    return Router(routes=routes)


@pytest.fixture
def client(config, app):
    config.templates = deepcopy(config.templates)
    config.templates.env.globals["static_url_for"] = lambda name, path: path
    return TestClient(app)


class TestHomeEndpoint:
    def test_ok(self, client):
        response = client.get("/")
        assert response.status_code == HTTPStatus.OK


class TestReadEndpoint:
    def test_not_found(self, client):
        with pytest.raises(HTTPException, match="NOT_FOUND"):
            client.get("/test")

    def test_read(self, client, redis, s3):
        redis.hgetall.return_value = {b"secret_hash": b"s", b"title": b"Test"}
        s3.get_object.return_value = mocks.MockS3Response(text="c", status=200)

        response = client.get("/test")

        assert response.status_code == HTTPStatus.OK

        assert isinstance(response.context["request"], Request)
        assert response.context["title"] == "Test"
        assert response.context["content"] == "c"


class TestPublishEndpoint:
    def test_not_unique(self, client, redis):
        redis.exists.return_value = True

        response = client.post(
            "/api/publish", json={"title": "Test", "content": "<p>test</p>"}
        )
        assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY

        data = response.json()
        assert data["title"] == ["is already being used"]

    def test_publish(self, client, redis, s3):
        redis.exists.return_value = False

        response = client.post(
            "/api/publish", json={"title": "Test", "content": "<script>"}
        )

        redis.hset.assert_awaited_once()
        redis.hset.await_args.args == ["metadata:test"]

        assert len(redis.hset.await_args.kwargs) == 1
        assert "mapping" in redis.hset.await_args.kwargs

        mapping = redis.hset.await_args.kwargs["mapping"]
        assert isinstance(mapping["secret_hash"], str)
        assert mapping["title"] == "Test"

        s3.put_object.assert_awaited_once()

        assert response.status_code == HTTPStatus.OK

        data = response.json()
        assert isinstance(data["secret"], str)
        assert isinstance(data["url"], str)

        assert crypt_context.verify(data["secret"], mapping["secret_hash"])


class TestUpdateEndpoint:
    def test_not_found(self, client, redis):
        redis.hgetall.return_value = None

        with pytest.raises(HTTPException, match="NOT_FOUND"):
            client.post(
                "/api/test/update", json={"secret": "secret", "content": "<p>test</p>"}
            )

    def test_incorrect_password(self, client, redis):
        redis.hgetall.return_value = {
            b"secret_hash": b"$2b$12$kbGqdxpfbOCDxiVO7Dupee635ot/7PxgaQtStZwI7Lb4aQqLoNI8S"
        }

        response = client.post(
            "/api/test/update", json={"secret": "incorrect", "content": "<p>test</p>"}
        )

        assert response.status_code == 422

    def test_ok(self, client, redis, s3):
        redis.hgetall.return_value = {
            b"secret_hash": b"$2b$12$kbGqdxpfbOCDxiVO7Dupee635ot/7PxgaQtStZwI7Lb4aQqLoNI8S"
        }

        response = client.post(
            "/api/test/update",
            json={
                "secret": "-2pTK-KBRQn7IDNMzm3oJBbAiI1QU_jC_fAz9TuZI18",
                "content": "<p>test</p>",
            },
        )

        s3.put_object.assert_awaited_once()

        assert response.status_code == 200

        data = response.json()

        assert len(data) == 1
        assert "test" in data["url"]


class TestDeleteEndpoint:
    def test_not_found(self, client, redis):
        redis.hgetall.return_value = None

        with pytest.raises(HTTPException, match="NOT_FOUND"):
            client.post("/api/test/delete", json={"secret": "secret"})

    def test_incorrect_password(self, client, redis):
        redis.hgetall.return_value = {
            b"secret_hash": b"$2b$12$kbGqdxpfbOCDxiVO7Dupee635ot/7PxgaQtStZwI7Lb4aQqLoNI8S"
        }

        response = client.post("/api/test/delete", json={"secret": "incorrect"})

        assert response.status_code == 422

    def test_ok(self, client, redis, s3):
        redis.hgetall.return_value = {
            b"secret_hash": b"$2b$12$kbGqdxpfbOCDxiVO7Dupee635ot/7PxgaQtStZwI7Lb4aQqLoNI8S"
        }

        response = client.post(
            "/api/test/delete",
            json={
                "secret": "-2pTK-KBRQn7IDNMzm3oJBbAiI1QU_jC_fAz9TuZI18",
            },
        )

        redis.delete.assert_awaited_once()
        s3.remove_object.assert_awaited_once()

        assert response.status_code == 200


class TestHealthEndpoint:
    def test_ok(self, client, redis):
        redis.ping.return_value = True

        response = client.get("/api/health")
        assert response.status_code == HTTPStatus.OK
        assert response.json() == {"redis": True}
