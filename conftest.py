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
