import asyncclick as click
import uvicorn
from fastapi_static_digest import StaticDigestCompiler

from easypub import config
from easypub.endpoints import content_bucket


async def _make_bucket():
    buckets = await config.s3.list_buckets()

    if content_bucket not in buckets:
        await config.s3.make_bucket(content_bucket)


@click.group()
def cli():
    pass


@cli.command()
async def runserver():
    await _make_bucket()

    uvicorn.run(
        "easypub.asgi:app",
        reload=True,
        reload_includes=["*.py", "*.html", "*.js", "*.css"],
        reload_excludes=["_digest/**"],
    )


@cli.command()
def collectstatic():
    StaticDigestCompiler(config.base_dir / "static").compile()


@cli.command()
async def makebucket():
    await _make_bucket()
