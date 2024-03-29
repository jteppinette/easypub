import json
from pathlib import Path

from fastapi_static_digest import StaticDigest
from jinja2.filters import do_mark_safe
from miniopy_async import Minio
from pydantic import AnyHttpUrl, BaseSettings, RedisDsn
from redis.asyncio import Redis
from slowapi import Limiter

from starlette.templating import Jinja2Templates

from easypub.utils import cached_property, get_client_ip


class Config(BaseSettings):
    cache_url: RedisDsn
    debug: bool = False
    host: str
    request_timeout: int = 5
    storage_url: AnyHttpUrl

    @cached_property
    def base_dir(self):
        return Path(__file__).resolve().parent

    @cached_property
    def templates(self):
        jinja = Jinja2Templates(directory=self.base_dir / "templates")

        # Add the jsonify filter to the environment. This filter will json encode
        # and mark the resulting text as safe. This can be used to template
        # javascript configuration.
        jinja.env.filters["jsonify"] = lambda v: do_mark_safe(json.dumps(v))

        return jinja

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
            key_func=get_client_ip,
            enabled=not self.debug,
            storage_uri=self.cache_url,
        )

    @cached_property
    def s3(self):
        if self.storage_url.port:
            endpoint = f"{self.storage_url.host}:{self.storage_url.port}"
        else:
            endpoint = self.storage_url.host

        return Minio(
            endpoint=endpoint,
            access_key=self.storage_url.user,
            secret_key=self.storage_url.password,
            secure=self.storage_url.scheme == "https",
        )

    @property
    def content_bucket(self):
        return self.storage_url.path.strip("/")

    @property
    def cache_control(self):
        return not self.debug

    @property
    def logging(self):
        access_logs_enabled = self.debug

        return {
            "version": 1,
            "disable_existing_loggers": False,
            "handlers": {"console": {"class": "logging.StreamHandler"}},
            "loggers": {
                "": {"handlers": ["console"], "level": "INFO"},
                "uvicorn.access": {"propagate": access_logs_enabled},
            },
        }
