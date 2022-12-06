import asyncclick as click
import uvicorn
from fastapi_static_digest import StaticDigestCompiler

from easypub import config


@click.group()
def cli():
    pass


@cli.command()
def runserver():
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
    buckets = await config.s3.list_buckets()
    if not buckets:
        await config.s3.make_bucket("posts")
