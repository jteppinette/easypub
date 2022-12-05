import secrets
import string
from http import HTTPStatus

from passlib.context import CryptContext
from pydantic import BaseModel

from starlette.endpoints import HTTPEndpoint
from starlette.exceptions import HTTPException
from starlette.responses import JSONResponse

from easypub import config
from easypub.fields import SafeHTML, Slug

crypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

limiter = config.limiter  # type: ignore


def generate_post_creds() -> tuple[str, str]:
    secret = secrets.token_urlsafe()
    return secret, crypt_context.hash(secret)


def verify_crypt_hash(secret: str, secret_hash: str) -> bool:
    return crypt_context.verify(secret, secret_hash)


def post_key(slug: str) -> str:
    if not slug:
        raise ValueError("slug must be a non-empty string")

    return f"post:{slug}"


class HomeEndpoint(HTTPEndpoint):
    async def get(self, request):
        return config.templates.TemplateResponse("index.html", {"request": request})


class ReadEndpoint(HTTPEndpoint):
    @limiter.limit("10/minute")
    async def get(self, request):
        slug = request.path_params["slug"]
        title = string.capwords(slug.replace("-", " "))

        result = await config.redis.hgetall(post_key(slug))
        if not result:
            raise HTTPException(HTTPStatus.NOT_FOUND)

        return config.templates.TemplateResponse(
            "read.html",
            {
                "request": request,
                "title": title,
                "content": result[b"content"].decode(),
                "secret_hash": result[b"secret_hash"].decode(),
            },
        )


class PublishEndpoint(HTTPEndpoint):
    class Form(BaseModel):
        slug: Slug
        content: SafeHTML

    @limiter.limit("60/hour")
    async def post(self, request):
        form = self.Form.parse_obj(await request.json())

        if await config.redis.exists(post_key(form.slug)):
            return JSONResponse(
                {"slug": ["is used by another post"]},
                status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            )

        secret, secret_hash = generate_post_creds()

        await config.redis.hset(
            post_key(form.slug),
            mapping={"content": form.content, "secret_hash": secret_hash},
        )

        return JSONResponse(
            dict(
                secret=secret,
                url=str(request.url.replace(path=form.slug)),
            )
        )


class HealthEndpoint(HTTPEndpoint):
    @limiter.limit("20/minute")
    async def get(self, request):
        return JSONResponse({"redis": await config.redis.ping()})
