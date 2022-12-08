import gzip
import io
import secrets
from http import HTTPStatus

from passlib.context import CryptContext
from pydantic import BaseModel, SecretStr
from slugify import slugify

from starlette.endpoints import HTTPEndpoint
from starlette.exceptions import HTTPException
from starlette.responses import JSONResponse

from easypub import config
from easypub.decorators import cache_control
from easypub.fields import SafeHTML, Title

crypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

limiter = config.limiter

content_bucket = "content"


def generate_post_creds() -> tuple[str, str]:
    secret = secrets.token_urlsafe()
    return secret, crypt_context.hash(secret)


def verify_crypt_hash(secret: str, secret_hash: str) -> bool:
    return crypt_context.verify(secret, secret_hash)


def metadata_key(slug: str) -> str:
    if not slug:
        raise ValueError("slug must be a non-empty string")

    return f"metadata:{slug}"


class HomeEndpoint(HTTPEndpoint):
    @cache_control(max_age="1h")
    async def get(self, request):
        return config.templates.TemplateResponse("index.html", {"request": request})


class ReadEndpoint(HTTPEndpoint):
    @limiter.limit("10/minute")
    @cache_control(max_age="1h")
    async def get(self, request):
        slug = request.path_params["slug"]

        result = await config.redis.hgetall(metadata_key(slug))
        if not result:
            raise HTTPException(HTTPStatus.NOT_FOUND)

        async with await config.s3.get_object(content_bucket, slug) as response:
            content = await response.text()

        return config.templates.TemplateResponse(
            "read.html",
            {
                "content": content,
                "request": request,
                "slug": slug,
                "title": result[b"title"].decode(),
            },
        )


class AdminEndpoint(HTTPEndpoint):
    @limiter.limit("10/minute")
    @cache_control(max_age="1h")
    async def get(self, request):
        slug = request.path_params["slug"]

        result = await config.redis.hgetall(metadata_key(slug))
        if not result:
            raise HTTPException(HTTPStatus.NOT_FOUND)

        content_url = await config.s3.get_presigned_url(
            "GET",
            content_bucket,
            slug,
        )

        return config.templates.TemplateResponse(
            "admin.html",
            {
                "content_url": content_url,
                "request": request,
                "slug": slug,
                "title": result[b"title"].decode(),
            },
        )


class PublishEndpoint(HTTPEndpoint):
    class Form(BaseModel):
        title: Title
        content: SafeHTML

    @limiter.limit("60/hour")
    async def post(self, request):
        form = self.Form.parse_obj(await request.json())
        slug = slugify(form.title)

        if await config.redis.exists(metadata_key(slug)):
            return JSONResponse(
                {"title": ["is already being used"]},
                status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            )

        secret, secret_hash = generate_post_creds()

        await config.redis.hset(
            metadata_key(slug),
            mapping={"secret_hash": secret_hash, "title": form.title},
        )

        encoded_content = gzip.compress(form.content.encode())
        await config.s3.put_object(
            content_bucket,
            slug,
            io.BytesIO(encoded_content),
            len(encoded_content),
            content_type="text/html",
            metadata={"content-encoding": "gzip"},
        )

        return JSONResponse(
            dict(
                secret=secret,
                url=request.url_for("read", slug=slug),
            )
        )


class UpdateEndpoint(HTTPEndpoint):
    class Form(BaseModel):
        secret: SecretStr
        content: SafeHTML

    @limiter.limit("60/hour")
    async def post(self, request):
        slug = request.path_params["slug"]
        form = self.Form.parse_obj(await request.json())

        result = await config.redis.hgetall(metadata_key(slug))
        if not result:
            raise HTTPException(HTTPStatus.NOT_FOUND)

        if not verify_crypt_hash(
            form.secret.get_secret_value(), result[b"secret_hash"].decode()
        ):
            return JSONResponse(
                {"secret": ["is incorrect"]},
                status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            )

        encoded_content = gzip.compress(form.content.encode())
        await config.s3.put_object(
            content_bucket,
            slug,
            io.BytesIO(encoded_content),
            len(encoded_content),
            content_type="text/html",
            metadata={"content-encoding": "gzip"},
        )

        return JSONResponse(dict(url=request.url_for("read", slug=slug)))


class DeleteEndpoint(HTTPEndpoint):
    class Form(BaseModel):
        secret: SecretStr

    @limiter.limit("10/hour")
    async def post(self, request):
        slug = request.path_params["slug"]
        form = self.Form.parse_obj(await request.json())

        result = await config.redis.hgetall(metadata_key(slug))
        if not result:
            raise HTTPException(HTTPStatus.NOT_FOUND)

        if not verify_crypt_hash(
            form.secret.get_secret_value(), result[b"secret_hash"].decode()
        ):
            return JSONResponse(
                {"secret": ["is incorrect"]},
                status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            )

        await config.redis.delete(metadata_key(slug))
        await config.s3.remove_object(content_bucket, slug)

        return JSONResponse({}, status_code=200)


class HealthEndpoint(HTTPEndpoint):
    @limiter.limit("20/minute")
    async def get(self, request):
        return JSONResponse({"redis": await config.redis.ping()})
