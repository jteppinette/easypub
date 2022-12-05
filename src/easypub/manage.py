from pathlib import Path

import asyncclick as click
import uvicorn
from fastapi_static_digest import StaticDigestCompiler

base_dir = Path(__file__).resolve().parent


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
    StaticDigestCompiler(base_dir / "static").compile()
