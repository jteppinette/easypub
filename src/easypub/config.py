from pathlib import Path

from fastapi_static_digest import StaticDigest
from pydantic import BaseSettings, RedisDsn
from redis.asyncio import Redis
from slowapi import Limiter
from slowapi.util import get_remote_address

from starlette.templating import Jinja2Templates

from easypub.utils import cached_property


class Config(BaseSettings):
    debug: bool = False
    request_timeout: int = 5
    cache_url: RedisDsn

    @cached_property
    def base_dir(self):
        return Path(__file__).resolve().parent

    @cached_property
    def templates(self):
        return Jinja2Templates(directory=self.base_dir / "templates")

    @cached_property
    def static(self):
        static = StaticDigest(source_dir=self.base_dir / "static")
        static.register_static_url_for(self.templates)
        return static

    @cached_property
    def redis(self):
        return Redis.from_url(self.cache_url)

    @cached_property
    def limiter(self):
        return Limiter(
            key_func=get_remote_address,
            enabled=not self.debug,
            storage_uri=self.cache_url,
        )
