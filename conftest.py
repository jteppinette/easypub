from unittest.mock import DEFAULT, AsyncMock, patch

import pytest

from easypub import config as appconfig


@pytest.fixture
def config():
    class Proxy:
        backup = {}

        def __setattr__(self, name, value):
            if name in appconfig.__dict__ and name not in self.backup:
                self.backup[name] = appconfig.__dict__[name]

            appconfig.__dict__[name] = value

        def __getattr__(self, name):
            return getattr(appconfig, name)

        def unwind(self):
            for name, value in self.backup.items():
                appconfig.__dict__[name] = value

    proxy = Proxy()
    yield proxy
    proxy.unwind()


@pytest.fixture
def redis(config):
    with patch.multiple(
        config.redis,
        new_callable=AsyncMock,
        delete=DEFAULT,
        exists=DEFAULT,
        hgetall=DEFAULT,
        hset=DEFAULT,
        ping=DEFAULT,
    ):
        yield config.redis


@pytest.fixture
def s3(config):
    with patch.multiple(
        config.s3,
        new_callable=AsyncMock,
        get_object=DEFAULT,
        get_presigned_url=DEFAULT,
        put_object=DEFAULT,
        remove_object=DEFAULT,
    ):
        yield config.s3
